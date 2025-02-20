// Function to load the chat conversation dynamically
async function loadConversation(phone) {
  try {
    const response = await fetch(`http://127.0.0.1:8000/get-messages/${phone}`);
    const data = await response.json();

    let chatMessages = document.getElementById("chatMessages");
    let chatTitle = document.getElementById("chatTitle");

    const contactName = data.name ? data.name : phone;
    const profilePic = data.profile_pic ? data.profile_pic : "user.png";  // Default image if none provided
    
    chatTitle.innerHTML = `
      <div class="d-flex align-items-center">
        <div class="me-3">
          <img src="${profilePic}" class="rounded-circle" width="40" onerror="this.src='user.png';">
        </div>
        <div>
          <strong>${contactName}</strong>
        </div>
      </div>
    `;

    // Clear old messages
    chatMessages.innerHTML = `<h4></h4>`;

    if (data.conversation && Array.isArray(data.conversation)) {
      let messagesHTML = data.conversation.map(msg => {
        let formattedMessage = msg.text.replace(/\n/g, "<br>");
        
        let isoTimestamp = msg.timestamp.replace(" ", "T");
        let date = new Date(isoTimestamp);
        let formattedTime = date.toLocaleString('en-US', {
          year: 'numeric',
          month: '2-digit',
          day: '2-digit',
          hour: '2-digit',
          minute: '2-digit',
          hour12: true
        });

        let timestampHTML = `<span class="timestamp">${formattedTime}</span>`;
        
        let messageClass = msg.direction.toLowerCase() === "sent" ? "message sent" : "message received";
        
        return `<div class="${messageClass}">${formattedMessage}<br>${timestampHTML}</div>`;
      }).join("");

      chatMessages.innerHTML += messagesHTML;
    } else {
      chatMessages.innerHTML += "<p>No messages found.</p>";
    }
  } catch (error) {
    console.error("Error loading conversation:", error);
    document.getElementById("chatMessages").innerHTML += "<p>Error loading messages.</p>";
  }

  document.getElementById("mainChat").style.display = "flex";
}

// Function to close the chat and show the empty state again
function closeChat() {
  document.getElementById("chatTitle").innerText = "WhatsApp-logs";
  document.getElementById("chatMessages").innerHTML = `
    <div class="empty-chat-message" id="emptyChat">
      <i class="fas fa-comments"></i>
      <p>Select a chat to start messaging</p>
    </div>
  `;
}

// Function to load chat list dynamically
async function loadChats() {
  const response = await fetch('http://127.0.0.1:8000/get-all-chats');
  const chats = await response.json();
  const chatListContainer = document.getElementById("chatItemsContainer");

  chatListContainer.innerHTML = ""; // Clear old chats

  chats.forEach(chat => {
    const chatItem = document.createElement('div');
    chatItem.classList.add('chat-item', 'p-2', 'd-flex', 'align-items-center', 'border-bottom');
    chatItem.setAttribute('data-phone', chat.phone);

    const contactName = chat.name ? chat.name : chat.phone;
    const profilePic = chat.profile_pic ? chat.profile_pic : "user.png";

    chatItem.innerHTML = `
      <div class="me-3">
        <img src="${profilePic}" class="rounded-circle" width="40" onerror="this.src='user.png';">
      </div>
      <div>
        <strong>${contactName}</strong>
      </div>
    `;

    chatItem.addEventListener('click', function () {
      loadConversation(chat.phone);
    });

    chatListContainer.appendChild(chatItem);
  });
}

// Load chat list when page loads
window.onload = loadChats;

// Listen for new messages from the WebSocket server
const socket = io.connect('http://127.0.0.1:8000');

socket.on('new_message', function(data) {
  loadChats(); // Refresh chat list to update profile pictures
  if (document.getElementById("chatTitle").innerText.includes(data.phone)) {
    loadConversation(data.phone); // Refresh chat if it's currently open
  }
});
