fetch(`/user_management/${userId}/delete`, {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': '{{ csrf_token() }}'  // Para Flask
    },
    body: JSON.stringify({})
})