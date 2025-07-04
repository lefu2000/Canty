        // Funcionalidad de búsqueda
        document.getElementById('search-bar').addEventListener('input', function() {
            const searchTerm = this.value.toLowerCase();
            const rows = document.querySelectorAll('.data-table tbody tr');
            
            rows.forEach(row => {
                const text = row.textContent.toLowerCase();
                row.style.display = text.includes(searchTerm) ? '' : 'none';
            });
        });

        // Botones de acción
        document.getElementById('logout-button').addEventListener('click', () => {
            window.location.href = "{{ url_for('logout') }}";
        });

        document.getElementById('load-file-button').addEventListener('click', () => {
            window.location.href = "Load.html"; /*Ruta Cargar Archivo*/
        });

        document.getElementById('create-new-device-button').addEventListener('click', () => {
            window.location.href = "layout_device.html"; /*Ruta Crear Nuevo Equipo*/
        });

        document.getElementById('register-button').addEventListener('click', () => {
            window.location.href = "Docs.html";
        });
        
        document.getElementById('documentation-button').addEventListener('click', () => {
            window.location.href = "Docs.html";
        });


        // Botones de eliminar
        document.querySelectorAll('.delete-btn').forEach(button => {
            button.addEventListener('click', function(e) {
                if(confirm('¿Estás seguro de que deseas eliminar este dispositivo?')) {
                    const row = this.closest('tr');
                    row.style.opacity = '0.5';
                    // Aquí iría la llamada AJAX para eliminar en el servidor
                }
                e.stopPropagation();
            });
        });

        // En dashboard_finish.html o en un archivo JS separado
        document.addEventListener('DOMContentLoaded', function() {
            // Validación de formulario de equipos
            const forms = document.querySelectorAll('form');
            forms.forEach(form => {
                form.addEventListener('submit', function(e) {
                    // Validar acrónimo
                    const acronimo = form.querySelector('#acronimo');
                    if (acronimo && !/^[A-Za-z]{3}-[A-Za-z]{3}-\d{2}$/.test(acronimo.value)) {
                        alert('El acrónimo debe tener el formato XXX-XXX-00 (3 letras, guión, 3 letras, guión, 2 números)');
                        e.preventDefault();
                        return false;
                    }
                    
                    // Validar IP
                    const ip = form.querySelector('#ip');
                    if (ip && !/^(\d{1,3}\.){3}\d{1,3}$/.test(ip.value)) {
                        alert('La dirección IP debe tener el formato XXX.XXX.XXX.XXX');
                        e.preventDefault();
                        return false;
                    }
                    
                    return true;
                });
            });
            
            // Confirmar eliminación
            const deleteButtons = document.querySelectorAll('.btn-delete');
            deleteButtons.forEach(button => {
                button.addEventListener('click', function(e) {
                    if (!confirm('¿Estás seguro de que deseas eliminar este equipo?')) {
                        e.preventDefault();
                    }
                });
            });
        });