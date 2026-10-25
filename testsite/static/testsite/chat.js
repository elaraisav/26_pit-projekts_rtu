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

    // WebSocket connection, reconnecting with a growing delay if it drops.
    let socket = null;
    let retryDelay = 1000;

    function connect() {
        const scheme = window.location.protocol === 'https:' ? 'wss' : 'ws';
        socket = new WebSocket(`${scheme}://${window.location.host}/ws/chat/${conversationId}/`);

        socket.addEventListener('open', function () {
            retryDelay = 1000;
            status.textContent = '';
            input.disabled = false;
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
