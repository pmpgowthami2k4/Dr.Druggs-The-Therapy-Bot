

document.addEventListener("DOMContentLoaded", function () {
    const menuToggle = document.getElementById("menu-toggle");
    const sidebar = document.getElementById("sidebar");

    // Check if sidebar was previously open
    if (localStorage.getItem("sidebarOpen") === "true") {
        sidebar.classList.add("active");
    }

    menuToggle.addEventListener("click", function () {
        sidebar.classList.toggle("active");

        // Store sidebar state in localStorage
        if (sidebar.classList.contains("active")) {
            localStorage.setItem("sidebarOpen", "true");
        } else {
            localStorage.setItem("sidebarOpen", "false");
        }
    });
});


///////////////////////////////////////////////////////////////////////////////////////////////////////
// Chat Elements
const chatBox = document.getElementById("chat-box");
const userInput = document.getElementById("user-input");
    userInput.addEventListener("keypress", function (event) {
        if (event.key === "Enter") {
            event.preventDefault();
            sendMessage();
        }
    });

// Function to Add Messages to Chat Window
function appendMessage(sender, message) {
    const messageDiv = document.createElement("div");
    messageDiv.classList.add("message", sender === "user" ? "user-message" : "bot-message");
    
    const messageText = document.createElement("p");
    messageText.innerText = message;
    messageDiv.appendChild(messageText);

    chatBox.appendChild(messageDiv);
    chatBox.scrollTop = chatBox.scrollHeight; // Auto-scroll to latest message
}

// Function to Send User Input to Flask API
async function sendMessage() {
    const message = userInput.value.trim();
    if (message === "") return;

    appendMessage("user", message); // Show user message
    userInput.value = "";

    try {
        const response = await fetch("http://127.0.0.1:5000/chat", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ message: message })
        });

        const data = await response.json();
        if (data.reply) {
            appendMessage("bot", data.reply);
        } else {
            appendMessage("bot", "Sorry, I couldn't process that.");
        }

    } catch (error) {
        console.error("Error:", error);
        appendMessage("bot", "Oops! Something went wrong. Please try again.");
    }
}



// Show Feel-Good List Modal with Data
async function showFeelGoodList() {
    try {
        const response = await fetch("http://127.0.0.1:5000/feel-good-lists");
        const data = await response.json();

        document.getElementById("feel-good-content").innerHTML = `
            <div class="feel-good-columns">
                <div class="column">
                    <h3>💬 Quote</h3>
                    <p>${data.quote}</p>
                </div>
                <div class="column">
                    <h3>🎵 Song Suggestion</h3>
                    <p>${data.song}</p>
                </div>
                <div class="column">
                    <h3>💡 Activity</h3>
                    <p>${data.activity}</p>
                </div>
            </div>
        `;

        // Show the modal
        document.getElementById("feel-good-modal").style.display = "block";
    } catch (error) {
        console.error("Error fetching Feel-Good Lists:", error);
        alert("Oops! Something went wrong. Please try again.");
    }
}

// Close the Modal
function closeFeelGoodList() {
    document.getElementById("feel-good-modal").style.display = "none";
}

// Function to Add Items to Lists
function addToList(type) {
    const input = document.getElementById(`${type}-input`);
    const value = input.value.trim();
    if (value === "") return;

    const list = document.getElementById(`${type}-list`);
    const listItem = document.createElement("li");
    listItem.classList.add("list-item");

    // ✅ Wrap text inside a span
    const textSpan = document.createElement("span");
    textSpan.textContent = value;

    // ✅ Create small, fixed delete button
    const deleteBtn = document.createElement("span");  // ✅ This is just an icon, not a button!
deleteBtn.classList.add("delete-icon");
deleteBtn.innerHTML = "✖";
    deleteBtn.innerHTML = "✖";
    deleteBtn.classList.add("delete-btn");

    deleteBtn.onclick = function () {
        list.removeChild(listItem);
    };

    listItem.appendChild(textSpan); // ✅ Text first
    listItem.appendChild(deleteBtn); // ✅ Small delete button (aligned right)
    list.appendChild(listItem);

    input.value = ""; // ✅ Clear input field
}
function removeItem(button) {
    button.parentElement.remove(); // ✅ Removes the correct list item
}


// Show Breathing Exercise Modal
// ✅ Prevent Multiple `setInterval` Calls
let breathingInterval;
const breathingTexts = ["Inhale... 😌", "Hold... 😮‍💨", "Exhale... 😌"];
let breathingIndex = 0;


function startBreathingCycle() {
    const breathingText = document.getElementById("breathing-text");
    if (!breathingText) return; // ✅ Prevents errors

    if (breathingInterval) clearInterval(breathingInterval); // ✅ Clear previous interval

    breathingInterval = setInterval(() => {
        breathingText.innerText = breathingTexts[breathingIndex];
        breathingIndex = (breathingIndex + 1) % breathingTexts.length;
    }, 1500);
}


function showBreathingExercise() {
    const modal = document.getElementById("breathing-modal");
    if (!modal) return;

    modal.style.display = "block"; // ✅ Show the modal
    startBreathingCycle(); // ✅ Start breathing exercise animation
}

function closeBreathingExercise() {
    const modal = document.getElementById("breathing-modal");
    if (!modal) return;

    modal.style.display = "none"; // ✅ Hide modal when closed
    clearInterval(breathingInterval); // ✅ Stop breathing animation
}


// RANDOM JOKE

// Show Random Joke Modal
async function showJokeModal() {
    try {
        const response = await fetch("https://official-joke-api.appspot.com/random_joke"); // ✅ Fetch random joke
        const data = await response.json();

        document.getElementById("joke-text").innerHTML = `<strong>${data.setup}</strong><br>${data.punchline}`;
        document.getElementById("joke-modal").style.display = "block"; // ✅ Show modal
    } catch (error) {
        console.error("Error fetching joke:", error);
        document.getElementById("joke-text").innerText = "Oops! Couldn't fetch a joke. Try again!";
    }
}

// Close Joke Modal
function closeJokeModal() {
    document.getElementById("joke-modal").style.display = "none";
}


// SNAKE MODAL
// ✅ Open Snake Game Modal
function showSnakeGame() {
    document.getElementById("snake-modal").style.display = "block";
    startGame(); // ✅ Start game from snake.js
}

// ✅ Close Snake Game Modal
function closeSnakeGame() {
    document.getElementById("snake-modal").style.display = "none";
    clearInterval(game); // ✅ Stop the game when modal closes
}



