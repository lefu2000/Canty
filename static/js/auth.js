document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('login-form');
    
    // Verificar si ya existe un elemento de error
    let errorElement = form.querySelector('.error-message');
    
    // Si no existe, crearlo
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
        const csrfToken = document.querySelector('[name="csrf_token"]').value;
        const submitBtn = form.querySelector('button[type="submit"]');
        
        // Validación
        if (!usuario || !contrasena) {
            showError('Por favor ingrese usuario y contraseña');
            return;
        }
        
        // Estado de carga
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<span class="spinner">Autenticando...</span>';
        
        try {
            const response = await fetch("/login", {
                method: 'POST',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'Accept': 'application/json'
                },
                body: new URLSearchParams({
                    usuario,
                    contrasena,
                    csrf_token: csrfToken
                })
            });

            // Verificar primero el estado de la respuesta
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || 'Error en la autenticación');
            }

            const data = await response.json();
            
            if (data.redirect) {
                window.location.href = data.redirect;
            }
        } catch (error) {
            showError(error.message || 'Error en el servidor');
            submitBtn.disabled = false;
            submitBtn.textContent = 'Iniciar Sesión';
        }
    });

    function showError(message) {
        errorElement.textContent = message;
        errorElement.style.display = 'block';
    }

        function showError(message) {
        errorElement.textContent = message;
        errorElement.style.display = 'block'; // Mostrar solo cuando haya error
    }
});