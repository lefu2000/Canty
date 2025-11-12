document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('login-form');
    
    // Crear elemento de error si no existe
    let errorElement = form.querySelector('.error-message');
    if (!errorElement) {
        errorElement = document.createElement('div');
        errorElement.className = 'error-message';
        errorElement.style.display = 'none';
        form.insertBefore(errorElement, form.firstChild);
    }

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const usuario = document.getElementById('usuario').value.trim();
        const contrasena = document.getElementById('contrasena').value.trim();
        const submitBtn = form.querySelector('button[type="submit"]');
        
        // Validación básica
        if (!usuario || !contrasena) {
            showError('Por favor ingrese usuario y contraseña');
            return;
        }
        
        // Estado de carga
        submitBtn.disabled = true;
        submitBtn.textContent = 'Autenticando...';
        hideError();
        
        try {
            // ✅ Usar FormData para incluir automáticamente el CSRF token
            const formData = new FormData(form);
            
            const response = await fetch("/login", {
                method: 'POST',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: formData
            });

            const data = await response.json();
            
            if (response.ok && data.success) {
                window.location.href = data.redirect;
            } else {
                showError(data.error || 'Error en la autenticación');
            }
        } catch (error) {
            showError('Error de conexión con el servidor');
            console.error('Error:', error);
        } finally {
            // ✅ Siempre restaurar el botón
            submitBtn.disabled = false;
            submitBtn.textContent = 'Iniciar Sesión';
        }
    });

    function showError(message) {
        errorElement.textContent = message;
        errorElement.style.display = 'block';
    }

    function hideError() {
        errorElement.style.display = 'none';
        errorElement.textContent = '';
    }
});
