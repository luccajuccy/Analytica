async function loadNotifications() {
    const stack = document.getElementById("notificationStack");
    if (!stack) return;
    window.closedNotificationIds = getClosedNotificationIds();
    try {
        const response = await fetch("/api/notifications?limit=3");
        const payload = await response.json();
        stack.innerHTML = (payload.notifications || [])
            .filter((item) => !window.closedNotificationIds.has(String(item.id)))
            .map((item) => `
            <div class="toast ${item.severity}" data-notification-id="${item.id}">
                <button class="toast-close" type="button" aria-label="Fechar notificacao" onclick="closeNotification('${item.id}')">x</button>
                <strong>${item.building_name}</strong>
                <div>${item.message}</div>
                <small>${item.created_at}</small>
            </div>
        `).join("");
    } catch (error) {
        stack.innerHTML = "";
    }
}

function closeNotification(id) {
    window.closedNotificationIds = getClosedNotificationIds();
    window.closedNotificationIds.add(String(id));
    sessionStorage.setItem("analyticaClosedNotifications", JSON.stringify([...window.closedNotificationIds]));
    const item = document.querySelector(`[data-notification-id="${id}"]`);
    if (item) item.remove();
}

function getClosedNotificationIds() {
    if (window.closedNotificationIds instanceof Set) {
        return window.closedNotificationIds;
    }
    try {
        return new Set(JSON.parse(sessionStorage.getItem("analyticaClosedNotifications") || "[]"));
    } catch (error) {
        return new Set();
    }
}

document.addEventListener("DOMContentLoaded", () => {
    loadNotifications();
    setInterval(loadNotifications, 30000);
});
