// 1) create channel table. table will have channel name, owner, admin and user, ban list, mute list,
// 2) create API to get channel details
// 3) create API to post and change settings (back end check for rights)
// 4) create a websocket to update all users of setting changes
// 5) list channels in the chat page. joined and unjoined channels
// 6) do front end 
// 7) check jwt for all api calls 

document.addEventListener('DOMContentLoaded', function () {
    let currentUser = localStorage.getItem('username');
    let recipientId;
    const chatSections = {};  // Store chat sections for each user
    
    const token = localStorage.getItem("accessToken");
    const usernamesDiv = document.getElementById('usernames');
    const chatHeader = document.getElementById('chat-header');
    const chatHeaderText = document.getElementById('chat-header-text');
    const chatInput = document.getElementById('chat-input-container');
    const blockButton = document.getElementById('block-button');

    fetch('/chat/usernames/', {            
      method: "GET",
      headers: {
          "Content-Type": "application/json",
          "Authorization": "Bearer " + token,
      },
    })
      .then(response => response.json())
      .then(usernames => {

        usernames.forEach(username => {
          if (username !== currentUser) {
            const chatTarget = document.createElement('p');
            chatTarget.textContent = username;
  
            chatTarget.onclick = () => {
              console.log('click');
              // Deselect previous selection
              const previouslySelected = document.querySelector('.user-list p.selected');
              if (previouslySelected) {
                previouslySelected.classList.remove('selected');
              }
              // Select the new user
              chatTarget.classList.add('selected');
              recipientId = username;
              chatHeaderText.textContent = recipientId;
  
              // Show or hide chat-header (bar above chat messages)
              if (chatHeaderText.textContent.trim() === '') {
                chatHeader.classList.remove('d-flex');
                chatHeader.classList.add('d-none');
              } else {
                chatHeader.classList.remove('d-none');
                chatHeader.classList.add('d-flex');
              }

              // set block button text based on blockArray. if user is blocked, text = 'Unblock'
              if (blockArray.includes(recipientId)) {
                blockButton.textContent = 'Click to Unblock';
              } else{
                blockButton.textContent = 'Click to Block';
              }

  
              // Switch chat container. div id = chat-messages-recipientId
              
              // hide all chat sections
              Object.values(chatSections).forEach(section => {
                section.classList.add('d-none');
                section.classList.remove('d-flex');
              });
              
              // if chat section not loaded, create it
              if (!chatSections[recipientId]) {
                const chatMessagesDiv = document.createElement('div');
                chatMessagesDiv.className = 'chat-messages flex-grow-1 p-3 overflow-auto';
                chatMessagesDiv.id = `chat-messages-${recipientId}`;
                chatSections[recipientId] = chatMessagesDiv;
                document.querySelector('.chat-section').insertBefore(chatMessagesDiv, document.querySelector('.chat-input-container'));
              }

              // show the recipient Id chat section
              if (!blockArray.includes(recipientId)) {
                chatSections[recipientId].classList.remove('d-none');
                chatSections[recipientId].classList.add('d-flex');
              }

              if (chatInput.classList.contains('d-none') && !blockArray.includes(recipientId)) {
                chatInput.classList.remove('d-none');
                chatInput.classList.add('d-flex');
              }
            };
            usernamesDiv.appendChild(chatTarget);
          }
        });
      });

    let blockArray = [];

    blockButton.addEventListener('click', function() {
      const indexOfRecipient = blockArray.indexOf(recipientId);
      
      if (indexOfRecipient === -1) {
        // User is not blocked, so block them
        blockArray.push(recipientId);
        // change button text
        blockButton.textContent = 'Click to Unblock';
        chatHeaderText.textContent = recipientId + ' (BLOCKED)';
        // remove chat input
        chatInput.classList.remove('d-flex');
        chatInput.classList.add('d-none');
        // remove chat section
        chatSections[recipientId].classList.remove('d-flex');
        chatSections[recipientId].classList.add('d-none');
        console.log(blockArray)
      } else {
        // User is blocked, so unblock them
        blockArray.splice(indexOfRecipient, 1);
        // change button text
        blockButton.textContent = 'Click to Block';
        chatHeaderText.textContent = recipientId;
        // remove chat input
        chatInput.classList.remove('d-none');
        chatInput.classList.add('d-flex');
        // remove chat section
        chatSections[recipientId].classList.remove('d-none');
        chatSections[recipientId].classList.add('d-flex');
        console.log(blockArray)
      }
    });


    // CHAT SOCKET

    const chatSocket = new WebSocket("wss://" + window.location.host + "/ws/chat/");
  
    function getTimeStamp(date) {
      const day = date.toLocaleString('en-US', { weekday: 'short' });
      const month = date.toLocaleString('en-US', { month: 'short' });
      const dayOfMonth = date.getDate().toString().padStart(2, '0');
      const year = date.getFullYear();
      const hours = date.getHours().toString().padStart(2, '0');
      const minutes = date.getMinutes().toString().padStart(2, '0');
      return `${dayOfMonth} ${month} ${year}, ${day} | ${hours}:${minutes}`;
    }
  
    chatSocket.onopen = function (e) {
      chatSocket.send(
        JSON.stringify({
          type: "username",
          content: currentUser,
        })
      );
      console.log("The connection was setup successfully!");
    };
  
    chatSocket.onclose = function (e) {
      console.log("Something unexpected happened!");
    };
  
    document.querySelector("#id_message_send_input").focus();
    document.querySelector("#id_message_send_input").onkeyup = function (e) {
      if (e.keyCode == 13) {
        document.querySelector("#id_message_send_button").click();
      }
    };
  
    document.querySelector("#id_message_send_button").onclick = function (e) {
      var messageInput = document.querySelector("#id_message_send_input").value;
      console.log(messageInput, recipientId);    
      if (!messageInput) {
        console.log("Cannot send an empty message or no recipient selected");
        return;
      }
      if (!recipientId) {
        console.log("No recipient selected");
        return;
      }
  
      var div = document.createElement("div");
      div.className = "chat-message sent";
      div.innerHTML = messageInput;
  
      var timestamp = document.createElement("div");
      timestamp.className = "timestamp sent";
      timestamp.innerHTML = getTimeStamp(new Date());
      div.appendChild(timestamp);
  
      chatSections[recipientId].appendChild(div);
      chatSections[recipientId].scrollTop = chatSections[recipientId].scrollHeight;
  
      chatSocket.send(
        JSON.stringify({
          type: "message",
          message: messageInput,
          recipient_id: recipientId,
        })
      );
  
      document.querySelector("#id_message_send_input").value = "";
    };
  
    chatSocket.onmessage = function (e) {
      const data = JSON.parse(e.data);
      console.log(data.sender, data.message);
      if (data.sender && data.message && !blockArray.includes(data.sender)) {
        if (!chatSections[data.sender]) {
          const chatMessagesDiv = document.createElement('div');
          chatMessagesDiv.className = 'chat-messages flex-grow-1 p-3 overflow-auto d-none';
          chatMessagesDiv.id = `chat-messages-${data.sender}`;
          chatSections[data.sender] = chatMessagesDiv;
          document.querySelector('.chat-section').insertBefore(chatMessagesDiv, document.querySelector('.chat-input-container'));
        }
  
        var div = document.createElement("div");
        div.className = "chat-message";
        div.innerHTML = `${data.message}`;
  
        var timestamp = document.createElement("div");
        timestamp.className = "timestamp";
        timestamp.innerHTML = getTimeStamp(new Date());
        div.appendChild(timestamp);
  
        chatSections[data.sender].appendChild(div);
        chatSections[data.sender].scrollTop = chatSections[data.sender].scrollHeight;
      }
    };
  });
  