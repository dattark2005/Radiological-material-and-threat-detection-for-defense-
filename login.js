// Login Page JavaScript
let isLoading = false;

// Initialize page
document.addEventListener('DOMContentLoaded', function() {
    // Check if already logged in
    const token = localStorage.getItem('authToken');
    if (token) {
        // Redirect to main dashboard if already authenticated
        window.location.href = 'index.html';
        return;
    }
    
    // Setup event listeners
    setupEventListeners();
    
    // Add some visual effects
    createFloatingParticles();
});

function setupEventListeners() {
    // Login form
    const loginForm = document.getElementById('loginForm');
    if (loginForm) {
        loginForm.addEventListener('submit', handleLogin);
    }
    
    // Register form
    const registerForm = document.getElementById('registerForm');
    if (registerForm) {
        registerForm.addEventListener('submit', handleRegister);
    }
    
    // Password confirmation validation
    const confirmPassword = document.getElementById('confirmPassword');
    if (confirmPassword) {
        confirmPassword.addEventListener('input', validatePasswordMatch);
    }
}

async function handleLogin(e) {
    e.preventDefault();
    
    if (isLoading) return;
    
    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;
    const rememberMe = document.getElementById('rememberMe').checked;
    
    if (!email || !password) {
        showNotification('Please fill in all fields', 'error');
        return;
    }
    
    setLoadingState(true);
    
    try {
        const response = await fetch('http://localhost:5000/api/auth/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                email: email,
                password: password
            })
        });
        
        const data = await response.json();
        
        if (response.ok && data.token) {
            // Store authentication token
            if (rememberMe) {
                localStorage.setItem('authToken', data.token);
                localStorage.setItem('userInfo', JSON.stringify(data.user));
            } else {
                sessionStorage.setItem('authToken', data.token);
                sessionStorage.setItem('userInfo', JSON.stringify(data.user));
            }
            
            showNotification('Login successful! Redirecting...', 'success');
            
            // Redirect to main dashboard after short delay
            setTimeout(() => {
                window.location.href = 'index.html';
            }, 1500);
            
        } else {
            showNotification(data.message || 'Login failed. Please check your credentials.', 'error');
        }
        
    } catch (error) {
        console.error('Login error:', error);
        showNotification('Connection error. Please check if the server is running.', 'error');
    } finally {
        setLoadingState(false);
    }
}

async function handleRegister(e) {
    e.preventDefault();
    
    if (isLoading) return;
    
    const email = document.getElementById('regEmail').value;
    const password = document.getElementById('regPassword').value;
    const confirmPassword = document.getElementById('confirmPassword').value;
    const role = document.getElementById('role').value;
    
    if (!email || !password || !confirmPassword || !role) {
        showNotification('Please fill in all fields', 'error');
        return;
    }
    
    if (password !== confirmPassword) {
        showNotification('Passwords do not match', 'error');
        return;
    }
    
    if (password.length < 6) {
        showNotification('Password must be at least 6 characters long', 'error');
        return;
    }
    
    setLoadingState(true, 'registerBtn');
    
    try {
        const response = await fetch('http://localhost:5000/api/auth/register', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                email: email,
                password: password,
                role: role
            })
        });
        
        const data = await response.json();
        
        if (response.ok && data.message && data.message.includes('successfully')) {
            showNotification('Registration successful! Please login with your credentials.', 'success');
            
            // Switch back to login form and pre-fill email
            setTimeout(() => {
                showLoginForm();
                document.getElementById('email').value = email;
            }, 2000);
            
        } else {
            showNotification(data.message || 'Registration failed. Please try again.', 'error');
        }
        
    } catch (error) {
        console.error('Registration error:', error);
        showNotification('Connection error. Please check if the server is running.', 'error');
    } finally {
        setLoadingState(false, 'registerBtn');
    }
}

function showLoginForm() {
    document.getElementById('loginForm').style.display = 'block';
    document.getElementById('registerForm').style.display = 'none';
    
    // Clear register form
    document.getElementById('regEmail').value = '';
    document.getElementById('regPassword').value = '';
    document.getElementById('confirmPassword').value = '';
    document.getElementById('role').value = '';
}

function showRegisterForm() {
    document.getElementById('loginForm').style.display = 'none';
    document.getElementById('registerForm').style.display = 'block';
}

function togglePassword() {
    const passwordInput = document.getElementById('password');
    const passwordIcon = document.getElementById('passwordIcon');
    
    if (passwordInput.type === 'password') {
        passwordInput.type = 'text';
        passwordIcon.className = 'fas fa-eye-slash';
    } else {
        passwordInput.type = 'password';
        passwordIcon.className = 'fas fa-eye';
    }
}

function validatePasswordMatch() {
    const password = document.getElementById('regPassword').value;
    const confirmPassword = document.getElementById('confirmPassword').value;
    const confirmInput = document.getElementById('confirmPassword');
    
    if (confirmPassword && password !== confirmPassword) {
        confirmInput.style.borderColor = '#ff4444';
        confirmInput.style.boxShadow = '0 0 15px rgba(255, 68, 68, 0.3)';
    } else {
        confirmInput.style.borderColor = '#333';
        confirmInput.style.boxShadow = 'none';
    }
}

function setLoadingState(loading, buttonId = 'loginBtn') {
    isLoading = loading;
    const button = document.getElementById(buttonId);
    
    if (loading) {
        button.classList.add('loading');
        button.disabled = true;
    } else {
        button.classList.remove('loading');
        button.disabled = false;
    }
}

function showNotification(message, type = 'info') {
    const notification = document.getElementById('notification');
    notification.textContent = message;
    notification.className = `notification ${type} show`;
    
    // Auto hide after 5 seconds
    setTimeout(() => {
        notification.classList.remove('show');
    }, 5000);
}

function createFloatingParticles() {
    const particles = document.querySelector('.particles');
    
    // Create additional floating particles
    for (let i = 0; i < 20; i++) {
        const particle = document.createElement('div');
        particle.style.position = 'absolute';
        particle.style.width = Math.random() * 4 + 1 + 'px';
        particle.style.height = particle.style.width;
        particle.style.background = `rgba(0, 255, 255, ${Math.random() * 0.5 + 0.1})`;
        particle.style.borderRadius = '50%';
        particle.style.left = Math.random() * 100 + '%';
        particle.style.top = Math.random() * 100 + '%';
        particle.style.animation = `particleFloat ${Math.random() * 10 + 10}s linear infinite`;
        particle.style.animationDelay = Math.random() * 5 + 's';
        
        particles.appendChild(particle);
    }
}

// Keyboard shortcuts
document.addEventListener('keydown', function(e) {
    // Enter key to submit active form
    if (e.key === 'Enter') {
        const loginForm = document.getElementById('loginForm');
        const registerForm = document.getElementById('registerForm');
        
        if (loginForm.style.display !== 'none') {
            handleLogin(e);
        } else if (registerForm.style.display !== 'none') {
            handleRegister(e);
        }
    }
    
    // Escape key to clear forms
    if (e.key === 'Escape') {
        document.getElementById('email').value = '';
        document.getElementById('password').value = '';
    }
});

// Demo credentials helper
document.addEventListener('keydown', function(e) {
    // Ctrl + D to fill demo credentials
    if (e.ctrlKey && e.key === 'd') {
        e.preventDefault();
        document.getElementById('email').value = 'admin@example.com';
        document.getElementById('password').value = 'admin123';
        showNotification('Demo credentials filled! Press Enter to login.', 'info');
    }
});
