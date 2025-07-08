# Inicio de sesión

fetch("https://192.168.1.10:11443/api/auth/login", {
  method: "POST",
  headers: {
    "Content-Type": "application/json"
  },
  body: JSON.stringify({ username: "mhyst", password: "telojuro12" })
})
  .then(res => res.json())
  .then(data => console.log(data))
  .catch(err => console.error(err));

# Recabar datos del usuario conectado

fetch("https://192.168.1.10:11443/api/user/me", {
  method: "GET",
  headers: {
    "Content-Type": "application/json",
    "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJmcmVzaCI6ZmFsc2UsImlhdCI6MTc1MTk4ODQ2OCwianRpIjoiY2EwZWMzNzUtMTEwNS00ZjQzLTk1YzMtNzA4ZDBhM2U3MDNhIiwidHlwZSI6ImFjY2VzcyIsInN1YiI6IjIiLCJuYmYiOjE3NTE5ODg0NjgsImNzcmYiOiJhMzliYzdlZC1iYjY3LTRkNjEtYjhlMC0zNTM1YTA5NjBiYjMiLCJleHAiOjE3NTE5OTIwNjgsInVzZXJuYW1lIjoibWh5c3QiLCJyb2xlIjoidXNlciJ9.lQ8av5fLa1ZA6Nzr9TC26q3h_CFMirMmJaT6H0JBM-Y
  }
})
  .then(res => res.json())
  .then(data => console.log(data))
  .catch(err => console.error(err));

# Modificar datos del usuario

fetch("https://192.168.1.10:11443/api/user/me", {
  method: "PATCH",
  headers: {
    "Content-Type": "application/json",
    "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJmcmVzaCI6ZmFsc2UsImlhdCI6MTc1MTk4ODQ2OCwianRpIjoiY2EwZWMzNzUtMTEwNS00ZjQzLTk1YzMtNzA4ZDBhM2U3MDNhIiwidHlwZSI6ImFjY2VzcyIsInN1YiI6IjIiLCJuYmYiOjE3NTE5ODg0NjgsImNzcmYiOiJhMzliYzdlZC1iYjY3LTRkNjEtYjhlMC0zNTM1YTA5NjBiYjMiLCJleHAiOjE3NTE5OTIwNjgsInVzZXJuYW1lIjoibWh5c3QiLCJyb2xlIjoidXNlciJ9.lQ8av5fLa1ZA6Nzr9TC26q3h_CFMirMmJaT6H0JBM-Y"
  },
  body: JSON.stringify({ password: "telojuro14" })
})
  .then(res => res.json())
  .then(data => console.log(data))
  .catch(err => console.error(err));

# Mostrar perfil público de un usuario

fetch("https://192.168.1.10:11443/api/user/1", {
  method: "GET",
  headers: {
    "Content-Type": "application/json",
    "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJmcmVzaCI6ZmFsc2UsImlhdCI6MTc1MTk4ODQ2OCwianRpIjoiY2EwZWMzNzUtMTEwNS00ZjQzLTk1YzMtNzA4ZDBhM2U3MDNhIiwidHlwZSI6ImFjY2VzcyIsInN1YiI6IjIiLCJuYmYiOjE3NTE5ODg0NjgsImNzcmYiOiJhMzliYzdlZC1iYjY3LTRkNjEtYjhlMC0zNTM1YTA5NjBiYjMiLCJleHAiOjE3NTE5OTIwNjgsInVzZXJuYW1lIjoibWh5c3QiLCJyb2xlIjoidXNlciJ9.lQ8av5fLa1ZA6Nzr9TC26q3h_CFMirMmJaT6H0JBM-Y"
  }
})
  .then(res => res.json())
  .then(data => console.log(data))
  .catch(err => console.error(err));

# Buscar usuarios por nombre

fetch("https://192.168.1.10:11443/api/users/search?query=Jua", {
  method: "GET",
  headers: {
    "Content-Type": "application/json",
    "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJmcmVzaCI6ZmFsc2UsImlhdCI6MTc1MTk4ODQ2OCwianRpIjoiY2EwZWMzNzUtMTEwNS00ZjQzLTk1YzMtNzA4ZDBhM2U3MDNhIiwidHlwZSI6ImFjY2VzcyIsInN1YiI6IjIiLCJuYmYiOjE3NTE5ODg0NjgsImNzcmYiOiJhMzliYzdlZC1iYjY3LTRkNjEtYjhlMC0zNTM1YTA5NjBiYjMiLCJleHAiOjE3NTE5OTIwNjgsInVzZXJuYW1lIjoibWh5c3QiLCJyb2xlIjoidXNlciJ9.lQ8av5fLa1ZA6Nzr9TC26q3h_CFMirMmJaT6H0JBM-Y"
  }
})
  .then(res => res.json())
  .then(data => console.log(data))
  .catch(err => console.error(err));


# Listar salas a las que está unido el usuario

fetch("https://192.168.1.10:11443/api/rooms", {
  method: "GET",
  headers: {
    "Content-Type": "application/json",
    "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJmcmVzaCI6ZmFsc2UsImlhdCI6MTc1MTk5MDg0MCwianRpIjoiMzFmYTM0OTAtZjk4ZC00YTZmLTkyOTItYWY1MzdjY2EyZmRlIiwidHlwZSI6ImFjY2VzcyIsInN1YiI6IjIiLCJuYmYiOjE3NTE5OTA4NDAsImNzcmYiOiIyNDFlMjc1NS1hZTgxLTQzMTctODIyZS1iNWY5ZGQ4NWM3NjMiLCJleHAiOjE3NTE5OTQ0NDAsInVzZXJuYW1lIjoibWh5c3QiLCJyb2xlIjoidXNlciJ9.RjCwEOQAinAlf55Adi2rwtGB1ASAVZkfhBC5QdBmxWw"
  }
})
  
  .then(res => res.json())
  .then(data => console.log(data))
  .catch(err => console.error(err));

# Crear sala

fetch("https://192.168.1.10:11443/api/rooms", {
  method: "POST",
  headers: {
    "Content-Type": "application/json",
    "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJmcmVzaCI6ZmFsc2UsImlhdCI6MTc1MTk5MDg0MCwianRpIjoiMzFmYTM0OTAtZjk4ZC00YTZmLTkyOTItYWY1MzdjY2EyZmRlIiwidHlwZSI6ImFjY2VzcyIsInN1YiI6IjIiLCJuYmYiOjE3NTE5OTA4NDAsImNzcmYiOiIyNDFlMjc1NS1hZTgxLTQzMTctODIyZS1iNWY5ZGQ4NWM3NjMiLCJleHAiOjE3NTE5OTQ0NDAsInVzZXJuYW1lIjoibWh5c3QiLCJyb2xlIjoidXNlciJ9.RjCwEOQAinAlf55Adi2rwtGB1ASAVZkfhBC5QdBmxWw"
  },
  body: JSON.stringify({ nombre: "Amigos", privada: false })
})
  
  .then(res => res.json())
  .then(data => console.log(data))
  .catch(err => console.error(err));

# Obtener información de sala

fetch("https://192.168.1.10:11443/api/rooms/1", {
  method: "GET",
  headers: {
    "Content-Type": "application/json",
    "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJmcmVzaCI6ZmFsc2UsImlhdCI6MTc1MTk5MDg0MCwianRpIjoiMzFmYTM0OTAtZjk4ZC00YTZmLTkyOTItYWY1MzdjY2EyZmRlIiwidHlwZSI6ImFjY2VzcyIsInN1YiI6IjIiLCJuYmYiOjE3NTE5OTA4NDAsImNzcmYiOiIyNDFlMjc1NS1hZTgxLTQzMTctODIyZS1iNWY5ZGQ4NWM3NjMiLCJleHAiOjE3NTE5OTQ0NDAsInVzZXJuYW1lIjoibWh5c3QiLCJyb2xlIjoidXNlciJ9.RjCwEOQAinAlf55Adi2rwtGB1ASAVZkfhBC5QdBmxWw"
  }
})
  
  .then(res => res.json())
  .then(data => console.log(data))
  .catch(err => console.error(err));
