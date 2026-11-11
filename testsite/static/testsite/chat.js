// Live chat on the terzetava page: shows the conversation history and
// sends/receives messages over a WebSocket (Django Channels, chat/consumers.py).
(function () {
    const main = document.querySelector('.chat-main[data-conversation-id]');
    if (!main) {
        return;
    }

    const conversationId = main.dataset.conversationId;
    const userId = Number(main.dataset.userId);
    const log = document.getElementById('chat-log');
    const emptyNote = document.getElementById('chat-empty');
    const form = document.getElementById('message-form');
    const input = document.getElementById('message-input');
    const status = document.getElementById('chat-status');
    const history = JSON.parse(document.getElementById('chat-history').textContent);

    // Papildinājum sdažada veida ziņojumu uzverei
    const paymentDialog = document.getElementById('payment-dialog');
    const payDialog = document.getElementById('pay-dialog');

    const paymentButton = document.getElementById('payment-btn');
    const imageButton = document.getElementById('image-btn');
    const imageInput = document.getElementById('image-input');

    let selectedPaymentId = null;
    const paymentElements = new Map();

    // Messages from the same person within 5 minutes share one group (name + time).
    const GROUP_GAP_MS = 5 * 60 * 1000;
    let lastGroup = null;

    // Ids of messages already on the page, so live and fetched messages never show twice.
    const shownIds = new Set();
    let lastId = 0;

    function formatTime(date) {
        const time = date.toLocaleTimeString('lv-LV', {hour: '2-digit', minute: '2-digit'});
        if (date.toDateString() === new Date().toDateString()) {
            return time;
        }
        return date.toLocaleDateString('lv-LV', {day: 'numeric', month: 'short'}) + ' ' + time;
    }

    function isNearBottom() {
        return log.scrollHeight - log.scrollTop - log.clientHeight < 80;
    }

    function scrollToBottom() {
        log.scrollTop = log.scrollHeight;
    }

    function sanitizeHttpUrl(raw) {
        if (typeof raw !== 'string' || raw.trim() === '') {
            return null;
        }
        try {
            const parsed = new URL(raw, window.location.origin);
            if (parsed.protocol === 'http:' || parsed.protocol === 'https:') {
                return parsed.href;
            }
        } catch (e) {
            return null;
        }
        return null;
    }

    function addMessage(message) {
        if (shownIds.has(message.id)) {
            return;
        }
        shownIds.add(message.id);
        lastId = Math.max(lastId, message.id);

        const created = new Date(message.created_at);
        const mine = message.sender_id === userId;

        if (emptyNote) {
            emptyNote.hidden = true;
        }

        if (!lastGroup || lastGroup.senderId !== message.sender_id || created - lastGroup.time > GROUP_GAP_MS) {
            const group = document.createElement('div');
            group.className = 'chat-message-group ' + (mine ? 'is-mine' : 'is-theirs');

            const sender = document.createElement('p');
            sender.className = 'chat-sender';
            sender.textContent = mine ? 'Tu' : message.sender_name;

            const time = document.createElement('time');
            time.className = 'chat-time';

            group.append(sender, time);
            log.append(group);
            lastGroup = {senderId: message.sender_id, element: group, timeElement: time};
        }

        // Ziņojuma saturs
        const bubble = document.createElement('article');
        bubble.className = 'chat-message';
        bubble.dataset.messageId = message.id;

        // Ja ziņas tips ir maksājums
        if (message.type === 'payment') {
            const card = document.createElement('div');
            card.className = 'chat-payment-card';

            const heading = document.createElement('strong');
            heading.textContent = 'Maksājuma pieprasījums';

            const amount = document.createElement('p');
            amount.textContent = message.amount + ' ' + message.currency;

            const paymentStatus = document.createElement('p');
            paymentStatus.className = 'payment-status';
            paymentStatus.textContent =
                message.payment_status === 'paid'
                    ? 'Apmaksāts'
                    : 'Gaida apmaksu';

            card.append(heading, amount, paymentStatus);
            if (!mine && message.payment_status === 'pending') {
                const payButton = document.createElement('button');
                payButton.type = 'button';
                payButton.textContent = 'Maksāt';

                payButton.addEventListener('click', function () {
                    selectedPaymentId = message.id;
                    payDialog.showModal();
                });
                card.append(payButton);
            }
            bubble.append(card);
            paymentElements.set(message.id, {
                status: paymentStatus,
                card: card
            });
        } else if (message.type === 'image') {
        // Ja ziņas tips ir attēls
            const card = document.createElement('div');
            card.className = 'chat-image-card';

            const safeImageUrl = sanitizeHttpUrl(message.image_url);
            if (!safeImageUrl) {
                const invalid = document.createElement('p');
                invalid.textContent = 'Nederīga attēla saite.';
                card.appendChild(invalid);
                bubble.appendChild(card);
                return;
            }

            const image = document.createElement('img');
            image.src = safeImageUrl;
            image.alt = 'Nosūtītais attēls';

            const download = document.createElement('a');
            download.href = safeImageUrl;
            download.download = '';
            download.textContent = 'Lejupielādēt';
            download.className = 'chat-download-btn';

            download.addEventListener('click', function () {
                status.textContent = 'Attēla lejupielāde sākta.';
            });

            card.append(image, download);
            bubble.appendChild(card);
        } else {
        // Ja vienkārša ziņa
            const text = document.createElement('p');
            text.textContent = message.text;
            bubble.append(text);
        }

        lastGroup.element.insertBefore(bubble, lastGroup.timeElement);

        lastGroup.time = created;
        lastGroup.timeElement.dateTime = message.created_at;
        lastGroup.timeElement.textContent = formatTime(created);
    }

    history.forEach(addMessage);
    scrollToBottom();

    // Fetches messages newer than the last one shown: those sent while the page
    // was loading or while the connection was down.
    function fetchMissed() {
        fetch(`/terzetava/${conversationId}/messages/?after=${lastId}`, {credentials: 'same-origin'})
            .then(function (response) {
                return response.ok ? response.json() : {messages: []};
            })
            .then(function (data) {
                const stick = isNearBottom();
                data.messages.forEach(addMessage);
                if (stick) {
                    scrollToBottom();
                }
            })
            .catch(function () {
                // The live connection still works; nothing else to do.
            });
    }

    // WebSocket connection, reconnecting with a growing delay if it drops.
    // If it never manages to open, 3 times in a row before the page was ever connected,
    // stop: the user is probably logged out or not allowed in this conversation.
    // After a successful connection, drops (e.g. a server restart) keep retrying.
    const MAX_REFUSED = 3;
    let socket = null;
    let retryDelay = 1000;
    let everOpened = false;
    let refusedInARow = 0;

    function connect() {
        const scheme = window.location.protocol === 'https:' ? 'wss' : 'ws';
        socket = new WebSocket(`${scheme}://${window.location.host}/ws/chat/${conversationId}/`);

        socket.addEventListener('open', function () {
            everOpened = true;
            refusedInARow = 0;
            retryDelay = 1000;
            status.textContent = '';
            input.disabled = false;
            fetchMissed();
        });

        // Papildināts dažādu ziņu apstrādei
        socket.addEventListener('message', function (event) {
            const data = JSON.parse(event.data);

            // Servera kļūda (piemēram, nederīga maksājuma summa)
            if (data.event === 'error') {
                status.textContent = data.error;
                return;
            }

            // Maksājuma statusa atjaunināšana
            if (data.event === 'payment_update') {
                const payment = data.message;
                const element = paymentElements.get(payment.id);
                if (element) {
                    element.status.textContent = 'Apmaksāts';
                    const button = element.card.querySelector('button');
                    if (button) {
                        button.remove();
                    }
                }
                return;
            }

            const stick = isNearBottom() || data.sender_id === userId;
            addMessage(data);
            if (stick) {
                scrollToBottom();
            }
        });

        socket.addEventListener('close', function () {
            input.disabled = true;
            if (!everOpened) {
                refusedInARow += 1;
                if (refusedInARow >= MAX_REFUSED) {
                    status.textContent = 'Neizdevās savienoties. Pārlādē lapu vai pieslēdzies vēlreiz.';
                    return;
                }
            }
            status.textContent = 'Savienojums pārtrūka. Mēģinu savienoties vēlreiz…';
            setTimeout(connect, retryDelay);
            retryDelay = Math.min(retryDelay * 2, 15000);
        });
    }

    form.addEventListener('submit', function (event) {
        event.preventDefault();
        const text = input.value.trim();
        if (!text) {
            return;
        }
        if (!socket || socket.readyState !== WebSocket.OPEN) {
            status.textContent = 'Nav savienojuma. Ziņa netika nosūtīta.';
            return;
        }
        socket.send(JSON.stringify({
            action: 'message',
            message: text
        }));
        input.value = '';
        input.focus();
    });

    // Atver maksājuma pieprasījuma logu
    if (paymentButton && paymentDialog) {
        paymentButton.addEventListener('click', function () {
            paymentDialog.showModal();
        });
    }

    // Nosūta maksājuma pieprasījumu
    document.getElementById('payment-submit')?.addEventListener('click', function () {
        const amount = document.getElementById('payment-amount').value;
        const currency = document.getElementById('payment-currency').value;
        if (!amount || Number(amount) <= 0) {
            status.textContent = 'Ievadiet derīgu summu.';
            return;
        }
        if (!socket || socket.readyState !== WebSocket.OPEN) {
            status.textContent = 'Nav savienojuma.';
            return;
        }
        socket.send(JSON.stringify({
            action: 'payment',
            amount: amount,
            currency: currency
        }));
        paymentDialog.close();
        status.textContent = '';
    });

    // Atver attēla izvēli
    if (imageButton) {
        imageButton.addEventListener('click', function () {
            imageInput.click();
        });
    }

    // Attēla augšupielāde
    imageInput.addEventListener('change', function () {
        const file = imageInput.files[0];
        if (!file) {
            return;
        }
        const formData = new FormData();
        formData.append('image', file);
        const csrfToken = form.querySelector(
            '[name=csrfmiddlewaretoken]'
        ).value;

        fetch(`/terzetava/${conversationId}/upload/`, {
            method: 'POST',
            body: formData,
            credentials: 'same-origin',
            headers: {
                'X-CSRFToken': csrfToken
            }
        })
        .then(async function (response) {
            const data = await response.json();
            if (!response.ok) {
                throw new Error(data.error || 'Neizdevās augšupielādēt attēlu.');
            }
            status.textContent = 'Attēls veiksmīgi augšupielādēts.';

            // Ja WebSocket jau piegādāja ziņu, dublikāts netiks attēlots.
            addMessage(data.message);
            scrollToBottom();
        })
        .catch(function (error) {
            status.textContent = error.message;
        })
        .finally(function () {
            imageInput.value = '';
        });
    });

    // Demonstrācijas apmaksa
    document.getElementById('pay-confirm').addEventListener('click', function () {
        if (!selectedPaymentId) {
            return;
        }
        const paymentInfo = document.getElementById('mock-payment-info').value.trim();
        if (!paymentInfo) {
            status.textContent = 'Ievadiet demonstrācijas maksājuma informāciju.';
            return;
        }
        if (!socket || socket.readyState !== WebSocket.OPEN) {
            status.textContent = 'Nav savienojuma.';
            return;
        }
        socket.send(JSON.stringify({
            action: 'pay',
            payment_id: selectedPaymentId
        }));
        payDialog.close();
        selectedPaymentId = null;

        status.textContent = 'Maksājums demonstrācijas režīmā apstiprināts.';
    });

    // Aizver dialoga logus
    document.querySelectorAll('[data-close-dialog]').forEach(function (button) {
        button.addEventListener('click', function () {
            button.closest('dialog').close();
        });
    });

    input.disabled = true;
    connect();
})();
