document.addEventListener("DOMContentLoaded", function () {
    // Establish a connection to the server using Socket.IO.
    var socket = io();
  
    socket.on('connect', function() {
      console.log("Connected to server via Socket.IO");
      // Load characters and environment when connected
      loadCharacters();
      loadEnvironment();
      loadScenePrompt();
      loadStyle();
    });
  
    // Listen for new image updates from the server
    socket.on('new_image', function(data) {
      console.log("Received new image update:", data);
      if (data && data.image_url) {
        updateSceneImage(data.image_url);
      } else {
        console.error("Received invalid image data:", data);
      }
    });
    
    // Listen for environment updates from the server
    socket.on('environment_update', function(data) {
      console.log("Received environment update:", data);
      if (data && data.description) {
        // Update the environment description in the UI
        const descriptionElement = document.getElementById('environment-description');
        if (descriptionElement) {
          descriptionElement.value = data.description;
        }
      } else {
        console.error("Received invalid environment data:", data);
      }
    });
    
    // Listen for scene prompt updates from the server
    socket.on('scene_prompt_update', function(data) {
      console.log("Received scene prompt update:", data);
      if (data && data.prompt !== undefined) {
        // Update the scene prompt in the UI
        updateScenePrompt(data.prompt);
      } else {
        console.error("Received invalid scene prompt data:", data);
      }
    });
    
    // Listen for style updates from the server
    socket.on('style_update', function(data) {
      console.log("Received style update:", data);
      if (data && data.style_data) {
        displayStyle(data.style_data);
      } else {
        console.error("Received invalid style data:", data);
      }
    });
    
    // Set up clear scene prompt button
    const clearScenePromptButton = document.getElementById('clear-scene-prompt');
    if (clearScenePromptButton) {
      clearScenePromptButton.addEventListener('click', clearScenePrompt);
    }
    
    // Set up style form functionality
    initStyleForms();

    // Add keyboard event listener for fullscreen toggle
    document.addEventListener('keydown', function(e) {
      // Toggle fullscreen on 'F' key or Escape
      if (e.key === 'f' || e.key === 'F') {
        toggleFullscreen();
      } else if (e.key === 'Escape') {
        const container = document.querySelector('.scene-container');
        if (container.classList.contains('fullscreen')) {
          toggleFullscreen();
        }
      }
    });
  
    function updateSceneImage(imageUrl) {
      var imageElement = document.getElementById("scene-image");
      if (imageElement) {
        console.log("Updating scene image with:", imageUrl);
        // First set opacity to 0 for fade effect
        imageElement.style.opacity = 0;
        
        // Create a new image object to preload
        var img = new Image();
        img.onload = function() {
          // Once loaded, update the src and fade in
          imageElement.src = imageUrl;
          setTimeout(() => {
            imageElement.style.opacity = 1;
          }, 50);
        };
        img.onerror = function() {
          console.error("Failed to load image:", imageUrl);
        };
        img.src = imageUrl;
      } else {
        console.error("Scene image element not found");
      }
    }
    
    function updateScenePrompt(promptText) {
      const promptElement = document.getElementById('scene-prompt-text');
      if (promptElement) {
        promptElement.textContent = promptText || "No scene has been generated yet.";
      }
    }
  
    async function clearScenePrompt() {
      try {
        const response = await fetch('/scene_prompt', {
          method: 'DELETE'
        });
        
        if (response.ok) {
          console.log('Scene prompt cleared successfully');
        } else {
          console.error('Error clearing scene prompt');
        }
      } catch (error) {
        console.error('Error clearing scene prompt:', error);
      }
    }
  
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

// Scene Prompt Management Functions
async function loadScenePrompt() {
    try {
        const response = await fetch('/scene_prompt');
        const data = await response.json();
        if (data.prompt) {
            updateScenePrompt(data.prompt);
        }
    } catch (error) {
        console.error('Error loading scene prompt:', error);
    }
}

function updateScenePrompt(promptText) {
    const promptElement = document.getElementById('scene-prompt-text');
    if (promptElement) {
        promptElement.textContent = promptText || "No scene has been generated yet.";
    }
}

// Environment Management Functions
async function loadEnvironment() {
    try {
        const response = await fetch('/environment');
        const environment = await response.json();
        displayEnvironment(environment);
    } catch (error) {
        console.error('Error loading environment:', error);
    }
}

function displayEnvironment(environment) {
    const descriptionElement = document.getElementById('environment-description');
    const lockElement = document.getElementById('environment-lock');
    
    if (descriptionElement) {
        descriptionElement.value = environment.description || '';
    }
    
    if (lockElement) {
        lockElement.checked = environment.locked || false;
    }
}

async function saveEnvironment() {
    const description = document.getElementById('environment-description').value;
    const locked = document.getElementById('environment-lock').checked;
    
    if (!description) {
        alert('Please provide an environment description');
        return;
    }
    
    try {
        const response = await fetch('/environment', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                description: description,
                locked: locked
            })
        });
        
        if (response.ok) {
            const updatedEnvironment = await response.json();
            displayEnvironment(updatedEnvironment);
            alert('Environment settings saved successfully');
        } else {
            alert('Error saving environment settings');
        }
    } catch (error) {
        console.error('Error saving environment:', error);
        alert('Error saving environment settings');
    }
}

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
            <div class="character-card-content">
                <h3>${data.name || id}</h3>
                <p><strong>ID:</strong> ${id}</p>
                <p>${data.description || 'No description provided.'}</p>
                <button onclick="editCharacter('${id}')">Edit</button>
                <button class="delete" onclick="deleteCharacter('${id}')">Delete</button>
            </div>
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
        alert('Please fill in all required fields');
        return;
    }
    
    try {
        const response = await fetch(`/characters/${id}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                name: name,
                description: description
            })
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

// Add the toggleFullscreen function
function toggleFullscreen() {
  const container = document.querySelector('.scene-container');
  const expandIcon = container.querySelector('.expand-icon');
  const compressIcon = container.querySelector('.compress-icon');
  
  container.classList.toggle('fullscreen');
  
  // Toggle icon visibility
  expandIcon.style.display = container.classList.contains('fullscreen') ? 'none' : 'block';
  compressIcon.style.display = container.classList.contains('fullscreen') ? 'block' : 'none';
  
  // Prevent scrolling when in fullscreen
  document.body.style.overflow = container.classList.contains('fullscreen') ? 'hidden' : '';
}

// Make toggleFullscreen available globally
window.toggleFullscreen = toggleFullscreen;

// Make environment functions available globally
window.saveEnvironment = saveEnvironment;

// Style Management Functions
async function loadStyle() {
    try {
        const response = await fetch('/style');
        const styleData = await response.json();
        displayStyle(styleData);
    } catch (error) {
        console.error('Error loading style settings:', error);
    }
}

function displayStyle(styleData) {
    // Update style text field with data from server
    if (!styleData) return;

    const styleTextField = document.getElementById('style-text');
    if (styleTextField && styleData.style_text) {
        styleTextField.value = styleData.style_text;
    }
}

async function saveStyle() {
    // Get value from the style text field
    const styleText = document.getElementById('style-text').value;
    
    if (!styleText) {
        alert('Please provide a style directive');
        return;
    }
    
    try {
        const response = await fetch('/style', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                style_text: styleText
            })
        });
        
        if (response.ok) {
            console.log('Style saved successfully');
            // The server will emit a style_update event that will update the UI
        } else {
            console.error('Error saving style');
            alert('Error saving style');
        }
    } catch (error) {
        console.error('Error saving style:', error);
        alert('Error saving style');
    }
}

async function resetStyle() {
    try {
        const response = await fetch('/style/reset', {
            method: 'POST'
        });
        
        if (response.ok) {
            const data = await response.json();
            console.log('Style reset successfully');
            // Update the UI with the reset values
            displayStyle(data.style_data);
        } else {
            console.error('Error resetting style');
            alert('Error resetting style');
        }
    } catch (error) {
        console.error('Error resetting style:', error);
        alert('Error resetting style');
    }
}

function initStyleForms() {
    // Add event listeners for the style form buttons
    document.getElementById('save-style')?.addEventListener('click', saveStyle);
    document.getElementById('reset-style')?.addEventListener('click', resetStyle);
}

// Make style functions available globally
window.saveStyle = saveStyle;
window.resetStyle = resetStyle;
  