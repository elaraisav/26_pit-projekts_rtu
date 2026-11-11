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

    let selectedPaymentId = null;
    const paymentElements = new Map();
    const statusLabels = {pending: 'Gaida apmaksu', paid: 'Apmaksāts', cancelled: 'Atcelts'};

    // What decides whether the photographer may add a batch of images: the latest
    // payment request must be paid and have no batch yet (the server checks it too).
    const payments = new Map();            // payment request id -> message
    const batchRequestIds = new Set();     // ids of the payment requests that already have a batch

    // Larger preview of the pictures of one batch, with arrows to step through them.
    const previewDialog = document.getElementById('preview-dialog');
    const previewImage = document.getElementById('preview-image');
    const previewCount = document.getElementById('preview-count');
    const previewPrev = document.getElementById('preview-prev');
    const previewNext = document.getElementById('preview-next');
    let previewItems = [];
    let previewIndex = 0;

    function showPreview() {
        previewImage.src = previewItems[previewIndex].preview;
        previewImage.alt = 'Attēls ' + (previewIndex + 1) + ' no ' + previewItems.length;
        previewCount.textContent = (previewIndex + 1) + ' / ' + previewItems.length;
    }

    function stepPreview(step) {
        previewIndex = (previewIndex + step + previewItems.length) % previewItems.length;
        showPreview();
    }

    function openPreview(items, index) {
        if (!previewDialog) {
            return;
        }
        previewItems = items;
        previewIndex = index;
        previewPrev.hidden = previewNext.hidden = items.length < 2;
        showPreview();
        previewDialog.showModal();
    }

    if (previewDialog) {
        previewPrev.addEventListener('click', function () {
            stepPreview(-1);
        });
        previewNext.addEventListener('click', function () {
            stepPreview(1);
        });
        previewDialog.addEventListener('keydown', function (event) {
            if (previewItems.length < 2) {
                return;
            }
            if (event.key === 'ArrowLeft') {
                stepPreview(-1);
            } else if (event.key === 'ArrowRight') {
                stepPreview(1);
            }
        });
        // A click on the dark background closes the preview.
        previewDialog.addEventListener('click', function (event) {
            if (event.target === previewDialog) {
                previewDialog.close();
            }
        });
    }

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
            paymentStatus.textContent = statusLabels[message.payment_status] || '';
            card.classList.toggle('is-cancelled', message.payment_status === 'cancelled');

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
            // The photographer can cancel a request that is not paid yet.
            if (mine && message.payment_status === 'pending') {
                const cancelButton = document.createElement('button');
                cancelButton.type = 'button';
                cancelButton.textContent = 'Atcelt';
                cancelButton.addEventListener('click', function () {
                    if (!socket || socket.readyState !== WebSocket.OPEN) {
                        status.textContent = 'Nav savienojuma.';
                        return;
                    }
                    socket.send(JSON.stringify({
                        action: 'cancel_payment',
                        payment_id: message.id
                    }));
                });
                card.append(cancelButton);
            }
            bubble.append(card);
            payments.set(message.id, message);
            paymentElements.set(message.id, {
                status: paymentStatus,
                card: card
            });
        } else if (message.type === 'image') {
            // Attēlu komplekts: small images (click for a larger preview) and the zip download under them.
            batchRequestIds.add(message.payment_request_id);

            const card = document.createElement('div');
            card.className = 'chat-image-card';

            const items = message.images
                .map(function (image) {
                    return {thumbnail: sanitizeHttpUrl(image.thumbnail), preview: sanitizeHttpUrl(image.preview)};
                })
                .filter(function (item) {
                    return item.thumbnail && item.preview;
                });

            const thumbs = document.createElement('div');
            thumbs.className = 'chat-thumbs';
            items.forEach(function (item, index) {
                const thumb = document.createElement('button');
                thumb.type = 'button';
                thumb.className = 'chat-thumb';
                thumb.setAttribute('aria-label', 'Atvērt attēlu ' + (index + 1) + ' no ' + items.length);

                const picture = document.createElement('img');
                picture.src = item.thumbnail;
                picture.alt = '';
                picture.loading = 'lazy';

                thumb.append(picture);
                thumb.addEventListener('click', function () {
                    openPreview(items, index);
                });
                thumbs.append(thumb);
            });
            card.append(thumbs);

            const archiveUrl = sanitizeHttpUrl(message.archive_url);
            if (archiveUrl) {
                const download = document.createElement('a');
                download.href = archiveUrl;
                // A readable file name instead of the random one on the server.
                download.download = 'attelu-komplekts-' + message.created_at.slice(0, 10) + '.zip';
                download.textContent = 'Lejupielādēt';
                download.className = 'chat-download-btn';
                card.append(download);
            }
            bubble.append(card);
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
        updateUploadButton();
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
                if (payments.has(payment.id)) {
                    payments.get(payment.id).payment_status = payment.payment_status;
                }
                updateUploadButton();
                const element = paymentElements.get(payment.id);
                if (element) {
                    element.status.textContent = statusLabels[payment.payment_status] || '';
                    element.card.classList.toggle('is-cancelled', payment.payment_status === 'cancelled');
                    // Paid or cancelled: no "Maksāt" or "Atcelt" button any more.
                    element.card.querySelectorAll('button').forEach(function (button) {
                        button.remove();
                    });
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

    // Upload is open when the latest payment request is paid and has no batch yet.
    function uploadOpen() {
        let latest = null;
        payments.forEach(function (payment) {
            if (!latest || payment.id > latest.id) {
                latest = payment;
            }
        });
        return latest !== null && latest.payment_status === 'paid' && !batchRequestIds.has(latest.id);
    }

    function updateUploadButton() {
        if (!imageButton) {
            return;
        }
        const open = uploadOpen();
        imageButton.disabled = !open;
        imageButton.title = open
            ? ''
            : 'Failus var pievienot, kad ir apmaksāts jaunākais maksājuma pieprasījums (viens komplekts par vienu pieprasījumu).';
    }
    updateUploadButton();

    // Attēlu komplekta augšupielāde: the button opens a dialog; the whole batch is sent
    // in one request and is accepted only if every file is valid.
    const uploadDialog = document.getElementById('upload-dialog');
    if (imageButton && uploadDialog) {
        const MAX_FILES = 10;
        const MAX_FILE_SIZE = 10 * 1024 * 1024;
        const filesInput = document.getElementById('upload-files');
        const countText = document.getElementById('upload-count');
        const fileList = document.getElementById('upload-list');
        const errorText = document.getElementById('upload-error');
        const submitButton = document.getElementById('upload-submit');
        let uploading = false;

        // Shows the chosen files and what is wrong with them; the upload button
        // works only for 1 to 10 valid files.
        function checkFiles() {
            const files = Array.from(filesInput.files);
            let problem = '';
            if (files.length > MAX_FILES) {
                problem = 'Vienā komplektā var būt ne vairāk kā ' + MAX_FILES + ' attēli.';
            }
            fileList.replaceChildren();
            files.forEach(function (file) {
                const valid = /\.(jpe?g|png)$/i.test(file.name) && file.size <= MAX_FILE_SIZE;
                if (!valid && !problem) {
                    problem = 'Daži faili nav derīgi (jābūt JPG vai PNG, līdz 10 MB). Izvēlies failus vēlreiz.';
                }
                const item = document.createElement('li');
                item.textContent = file.name + ' (' + (file.size / 1048576).toFixed(1) + ' MB)' + (valid ? '' : ' – nederīgs');
                fileList.append(item);
            });
            countText.textContent = files.length + ' / ' + MAX_FILES;
            errorText.textContent = problem;
            submitButton.disabled = uploading || files.length === 0 || problem !== '';
        }

        imageButton.addEventListener('click', function () {
            if (imageButton.disabled) {
                return;
            }
            filesInput.value = '';
            checkFiles();
            uploadDialog.showModal();
        });

        filesInput.addEventListener('change', checkFiles);

        submitButton.addEventListener('click', async function () {
            const files = Array.from(filesInput.files);
            if (uploading || files.length === 0) {
                return;
            }
            const formData = new FormData();
            files.forEach(function (file) {
                formData.append('images', file);
            });
            const csrfToken = form.querySelector('[name=csrfmiddlewaretoken]').value;

            uploading = true;
            submitButton.disabled = true;
            submitButton.textContent = 'Augšupielādē…';
            errorText.textContent = '';
            try {
                const response = await fetch(`/terzetava/${conversationId}/upload/`, {
                    method: 'POST',
                    body: formData,
                    credentials: 'same-origin',
                    headers: {'X-CSRFToken': csrfToken}
                });
                const data = await response.json().catch(function () {
                    return {};
                });
                if (!response.ok) {
                    errorText.textContent = data.error || 'Neizdevās augšupielādēt attēlus.';
                    return;
                }
                uploadDialog.close();
                status.textContent = 'Attēli augšupielādēti.';
                // The WebSocket may deliver the message first; a duplicate is not shown twice.
                addMessage(data.message);
                scrollToBottom();
            } catch (error) {
                errorText.textContent = 'Neizdevās augšupielādēt attēlus. Pārbaudi savienojumu.';
            } finally {
                uploading = false;
                submitButton.textContent = 'Augšupielādēt';
                checkFiles();
            }
        });
    }

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
