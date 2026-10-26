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

        // textContent, never innerHTML: messages are user input.
        const bubble = document.createElement('article');
        bubble.className = 'chat-message';
        const text = document.createElement('p');
        text.textContent = message.text;
        bubble.append(text);
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

        socket.addEventListener('message', function (event) {
            const message = JSON.parse(event.data);
            const stick = isNearBottom() || message.sender_id === userId;
            addMessage(message);
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
        socket.send(JSON.stringify({message: text}));
        input.value = '';
        input.focus();
    });

    input.disabled = true;
    connect();
})();
