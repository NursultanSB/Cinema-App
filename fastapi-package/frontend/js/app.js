const API_URL = "http://127.0.0.1:8000";

const getToken = () => localStorage.getItem("cinema_token");
const setToken = (t) => localStorage.setItem("cinema_token", t);
const removeToken = () => localStorage.removeItem("cinema_token");
const isAuthorized = () => !!getToken();

async function apiFetch(endpoint, options = {}) {
    options.headers = options.headers || {};
    const token = getToken();
    if (token) options.headers['Authorization'] = `Bearer ${token}`;
    
    if (options.body && typeof options.body === 'object' && !(options.body instanceof FormData)) {
        options.headers['Content-Type'] = 'application/json';
        options.body = JSON.stringify(options.body);
    }
    
    const res = await fetch(API_URL + '/api' + endpoint, options);
    if (res.status === 401) {
        removeToken();
        if (location.pathname.includes('profile')) location.href = 'login.html';
    }
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Произошла ошибка');
    return data;
}

const formatPrice = p => new Intl.NumberFormat('ru-RU').format(p) + ' ₸';
const formatDate = d => new Date(d).toLocaleDateString('ru-RU', { day: 'numeric', month: 'long', year: 'numeric' });

function logout() {
    removeToken();
    showToast("Вы вышли из системы", "success");
    setTimeout(() => { location.href = "login.html"; }, 1000);
}

function enforceAuth(pageName) {
    if (pageName === "profile.html" && !isAuthorized()) {
        location.href = "login.html";
    }
}

function renderNavigation() {
    const container = document.getElementById("main-nav");
    if (!container) return;
    const page = location.pathname.substring(location.pathname.lastIndexOf("/") + 1);
    const auth = isAuthorized();

    container.innerHTML = `
        <div class="nav-container">
            <a href="movies.html" class="logo">🍿 CinemaPass</a>
            <ul class="nav-menu">
                <li><a href="movies.html" class="nav-link ${page === 'movies.html' || page === '' ? 'active' : ''}">Афиша</a></li>
                ${auth ? `
                    <li><a href="profile.html" class="nav-link ${page === 'profile.html' ? 'active' : ''}">Мои билеты / Профиль</a></li>
                    <li><button onclick="logout()" class="btn-logout">Выйти</button></li>
                ` : `
                    <li><a href="login.html" class="nav-link ${page === 'login.html' ? 'active' : ''}">Войти</a></li>
                    <li><a href="register.html" class="nav-link ${page === 'register.html' ? 'active' : ''}">Регистрация</a></li>
                `}
            </ul>
        </div>
    `;
}

function showToast(message, type = "success") {
    let container = document.getElementById("toast-container");
    if (!container) {
        container = document.createElement("div");
        container.id = "toast-container";
        container.className = "toast-container";
        document.body.appendChild(container);
    }
    const toast = document.createElement("div");
    toast.className = `toast ${type}`;
    toast.innerHTML = `<span>${message}</span>`;
    container.appendChild(toast);
    setTimeout(() => {
        toast.style.opacity = "0";
        toast.style.transform = "translateY(20px)";
        toast.style.transition = "all 0.3s ease";
        setTimeout(() => toast.remove(), 300);
    }, 3500);
}

document.addEventListener("DOMContentLoaded", () => {
    const page = location.pathname.substring(location.pathname.lastIndexOf("/") + 1);
    enforceAuth(page);
    renderNavigation();
});
