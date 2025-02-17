// Function to load the chat conversation dynamically
async function loadConversation(phone) {
    const response = await fetch(`http://127.0.0.1:8000/get-messages/${phone}`);
    const data = await response.json();
    
    let chatMessages = document.getElementById("chatMessages");
    chatMessages.innerHTML = `<h4>Conversation with ${phone}</h4>`;

    if (data.conversation) {
        let messages = data.conversation.split("\n").map(msg => {
            let formattedMessage = msg.replace(/\n/g, "<br>");  // Fix new line display

            if (msg.startsWith('Me:')) {
                return `<div class="message sent">${formattedMessage}</div>`;
            } else if (msg.startsWith('Them:')) {
                return `<div class="message received">${formattedMessage}</div>`;
            } else {
                return `<div class="message">${formattedMessage}</div>`;
            }
        }).join('');
        
        chatMessages.innerHTML += messages;
    } else {
        chatMessages.innerHTML += "<p>No messages found.</p>";
    }

    // Show the main chat area and hide the chat list
    document.querySelector(".chat-list").style.display = "none";
    document.getElementById("mainChat").style.display = "flex";
}

// Function to load chat list dynamically
async function loadChats() {
    const response = await fetch('http://127.0.0.1:8000/get-all-chats');
    const chats = await response.json();
    const chatListContainer = document.getElementById("chatItemsContainer");

    chats.forEach(chat => {
        const chatItem = document.createElement('div');
        chatItem.classList.add('chat-item', 'p-2', 'd-flex', 'align-items-center', 'border-bottom');
        chatItem.setAttribute('data-phone', chat.phone);
        chatItem.innerHTML = `
            <div class="me-3"><img src="user.png" class="rounded-circle" width="40"></div>
            <div>
                <strong>${chat.phone}</strong>
                <p class="text-muted small mb-0">${chat.last_message || "No message"}</p>
            </div>
        `;
        chatItem.addEventListener('click', function () {
            loadConversation(chat.phone);
        });
        chatListContainer.appendChild(chatItem);
    });
}

// Function to close the chat and show the chat list again
function closeChat() {
    document.getElementById("mainChat").style.display = "none"; // Hide chat window
    document.querySelector(".chat-list").style.display = "flex"; // Show chat list
}

// Load chat list when page loads
window.onload = loadChats;

// Listen for new messages from the WebSocket server
const socket = io.connect('http://127.0.0.1:8000');

socket.on('message_received', function(data) {
    const chatTitle = document.getElementById('chatTitle').innerText.split(' ')[2];
    if (data.phone === chatTitle) {
        const chatMessages = document.getElementById("chatMessages");
        const messageElement = `
            <div class="message received">Them: ${data.message}</div>
        `;
        chatMessages.innerHTML += messageElement;
    }
});
