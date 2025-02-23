document.addEventListener("DOMContentLoaded", function () {
    // Establish a connection to the server using Socket.IO.
    var socket = io();
  
    socket.on('connect', function() {
      console.log("Connected to server via Socket.IO");
      // Load characters when connected
      loadCharacters();
    });
  
    // Listen for the "new_image" event.
    socket.on('new_image', function(data) {
      console.log("Received new image update:", data);
      if (data.image_url) {
        // Update the image element's source.
        var imageElement = document.getElementById("scene-image");
        // Adding a timestamp to the URL for cache busting.
        imageElement.src = data.image_url + "?t=" + new Date().getTime();
      }
    });
  
    // Optional: fallback mechanism to refresh periodically
    // setInterval(function(){
    //   location.reload();
    // }, 60000); // refresh page every 60 seconds if needed

    // Tab switching functionality
    document.querySelectorAll('.nav-tab').forEach(tab => {
      tab.addEventListener('click', () => {
        // Remove active class from all tabs and contents
        document.querySelectorAll('.nav-tab').forEach(t => t.classList.remove('active'));
        document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
        
        // Add active class to clicked tab and corresponding content
        tab.classList.add('active');
        document.getElementById(tab.dataset.tab + '-tab').classList.add('active');
      });
    });
});

// Character Management Functions
async function loadCharacters() {
    try {
        const response = await fetch('/characters');
        const characters = await response.json();
        displayCharacters(characters);
    } catch (error) {
        console.error('Error loading characters:', error);
    }
}

function displayCharacters(characters) {
    const characterList = document.getElementById('character-list');
    characterList.innerHTML = '';
    
    for (const [id, data] of Object.entries(characters)) {
        const card = document.createElement('div');
        card.className = 'character-card';
        card.innerHTML = `
            <h3>${data.name || id}</h3>
            <p><strong>ID:</strong> ${id}</p>
            <p>${data.description || 'No description provided.'}</p>
            <button onclick="editCharacter('${id}')">Edit</button>
            <button onclick="deleteCharacter('${id}')">Delete</button>
        `;
        characterList.appendChild(card);
    }
}

function editCharacter(id) {
    fetch(`/characters/${id}`)
        .then(response => response.json())
        .then(character => {
            document.getElementById('character-id').value = id;
            document.getElementById('character-name').value = character.name || '';
            document.getElementById('character-description').value = character.description || '';
        })
        .catch(error => console.error('Error loading character:', error));
}

async function saveCharacter() {
    const id = document.getElementById('character-id').value;
    const name = document.getElementById('character-name').value;
    const description = document.getElementById('character-description').value;
    
    if (!id || !name || !description) {
        alert('Please fill in all fields');
        return;
    }
    
    const characterData = {
        name: name,
        description: description
    };
    
    try {
        const response = await fetch(`/characters/${id}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(characterData)
        });
        
        if (response.ok) {
            loadCharacters();
            // Clear form
            document.getElementById('character-id').value = '';
            document.getElementById('character-name').value = '';
            document.getElementById('character-description').value = '';
        } else {
            alert('Error saving character');
        }
    } catch (error) {
        console.error('Error saving character:', error);
        alert('Error saving character');
    }
}

async function deleteCharacter(id) {
    if (!confirm(`Are you sure you want to delete character ${id}?`)) {
        return;
    }
    
    try {
        const response = await fetch(`/characters/${id}`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            loadCharacters();
        } else {
            alert('Error deleting character');
        }
    } catch (error) {
        console.error('Error deleting character:', error);
        alert('Error deleting character');
    }
}
  