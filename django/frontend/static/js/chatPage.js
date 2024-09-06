function showToast(message, duration = 3000) {
  // Create a div element for the toast message
  const toast = document.createElement('div');

  // Add text to the toast message
  toast.textContent = message;

  // Style the toast message
  toast.style.position = 'fixed';
  toast.style.top = '65px';
  toast.style.right = '20px';
  toast.style.padding = '10px';
  toast.style.color = 'white';
  toast.style.backgroundColor = 'green';
  toast.style.transition = 'opacity 0.5s';
  toast.style.opacity = '0';

  // Append the toast message to the body of the document
  document.body.appendChild(toast);

  // Fade in the toast message
  setTimeout(() => {
      toast.style.opacity = '1';
  }, 100); // This should match the duration of the transition

  // Fade out and remove the toast message after a certain amount of time
  setTimeout(() => {
      toast.style.opacity = '0';
      setTimeout(() => {
          toast.remove();
      }, duration); // This should match the duration of the transition
  }, duration);
}

// Function to create html for a new user 
function addUserToChatList(userID, username, chatTarget) {
  chatTarget.classList.add('d-flex', 'align-items-center'); // Apply Flexbox and center items vertically using Bootstrap classes
  chatTarget.id = `chat-target-${userID}`; // Add an id

  // Create the online status icon beside the username
  const statusIcon = document.createElement('span');
  statusIcon.classList.add('online-status-icon', 'mr-2'); // Add a class for styling and a Bootstrap class for margin
  statusIcon.id = `status-icon-${userID}`; // Add an id to the status icon
  statusIcon.textContent = '🔴'; // Use a green circle emoji as a simple online status icon
  statusIcon.style.fontSize = '8px'; // Change '10px' to the desired font size
  if (userID === '0') { // pong-bot
    statusIcon.style.fontSize = '12px'; // Change '10px' to the desired font size
    statusIcon.textContent = '💻';
    chatTarget.style.borderTop = '1px solid #ddd'; // Add a border to the bottom
    chatTarget.style.borderBottom = '1px solid #ddd'; // Add a border to the bottom
  }
if (userID !== "0" && !friendList.includes(userID)) {
    statusIcon.style.display = 'none';
}

  // Create the username text
  const usernameText = document.createElement('p');
  usernameText.classList.add('mb-0'); // Remove bottom margin from p element using Bootstrap class
  usernameText.textContent = username;            
  
  // Create the unread messages counter
  const unreadCounter = document.createElement('span');
  unreadCounter.id = `unread-counter-${userID}`; // Add an id to the counter
  unreadCounter.textContent = '0'; // Initialize the counter with 0 unread messages
  unreadCounter.style.marginLeft = '10px'; // Add some space between the username and the counter  
  unreadCounter.style.display = 'none';

  chatTarget.appendChild(statusIcon);
  chatTarget.appendChild(usernameText);
  chatTarget.appendChild(unreadCounter); // Append the counter to the chatTarget
}


// Function to set the onclick for any user in the chat list
function handleChatTargetClick (chatTarget, userID) {
  const chatHeader = document.getElementById('chat-header');
  const chatProfileButton = document.getElementById('chat-profile-button');
  const chatInput = document.getElementById('chat-input-container');
  const blockButton = document.getElementById('block-button');
  const friendButton = document.getElementById('friend-button');
  const inviteButton = document.getElementById('invite-button');

  chatTarget.onclick = () => {
    recipientId = userID;
    // Deselect previous selection
    const previouslySelected = document.querySelector('.user-list div.selected');
    if (previouslySelected) {
      previouslySelected.classList.remove('selected');
    }
    // Select the new user
    chatTarget.classList.add('selected');
    chatProfileButton.textContent = allUsers[userID];

    // Show or hide chat-header (bar above chat messages)
    if (chatProfileButton.textContent.trim() === '') {
      chatHeader.classList.remove('d-flex');
      chatHeader.classList.add('d-none');
    } else {
      chatHeader.classList.remove('d-none');
      chatHeader.classList.add('d-flex');
    }

    // set block button text based on blockArray. if user is blocked, text = 'Unblock'
    if (blockArray.includes(userID)) {
      blockButton.textContent = 'Click to Unblock';
      // remove chat input
      chatInput.classList.remove('d-flex');
      chatInput.classList.add('d-none');
      // remove chat section
      chatSections[userID].classList.remove('d-flex');
      chatSections[userID].classList.add('d-none');
    } else{
      blockButton.textContent = 'Click to Block';
    }

    // set block button text based on friendList. if user is friend, text = 'Unfriend'
    if (friendList.includes(userID)) {
      friendButton.textContent = 'Unfriend';
    } else{
      friendButton.textContent = 'Add Friend';
    }

    // set invite button text based on inviteArray.
    if (sendInviteArray.includes(userID)) {
      inviteButton.textContent = 'Invited. Click to cancel';
    }
    else
      inviteButton.textContent = 'Invite Player to Game';


    if (recieveInviteArray.includes(userID)) {
      inviteButton.textContent = 'Accept invite';
    }

    // reset unread counter
    const unreadCounter = document.getElementById(`unread-counter-${userID}`);
    unreadCounter.textContent = '0';
    unreadCounter.style.display = 'none';


    // Switch chat container. div id = chat-messages-recipientId
    
    // hide all chat sections
    Object.values(chatSections).forEach(section => {
      section.classList.add('d-none');
      section.classList.remove('d-flex');
    });
    
    // if chat section not loaded, create it
    if (!chatSections[userID]) {
      const chatMessagesDiv = document.createElement('div');
      chatMessagesDiv.className = 'chat-messages flex-grow-1 p-3 overflow-auto';
      chatMessagesDiv.id = `chat-messages-${userID}`;
      chatSections[userID] = chatMessagesDiv;
      document.querySelector('.chat-section').insertBefore(chatMessagesDiv, document.querySelector('.chat-input-container'));
    }

    // show the recipient Id chat section
    if (!blockArray.includes(userID)) {
      chatSections[userID].classList.remove('d-none');
      chatSections[userID].classList.add('d-flex');
    }

    if (chatInput.classList.contains('d-none') && !blockArray.includes(userID)) {
      chatInput.classList.remove('d-none');
      chatInput.classList.add('d-flex');
    }
  };
}

function getTimeStamp(date) {
  const day = date.toLocaleString('en-US', { weekday: 'short' });
  const month = date.toLocaleString('en-US', { month: 'short' });
  const dayOfMonth = date.getDate().toString().padStart(2, '0');
  const year = date.getFullYear();
  const hours = date.getHours().toString().padStart(2, '0');
  const minutes = date.getMinutes().toString().padStart(2, '0');
  return `${dayOfMonth} ${month} ${year}, ${day} | ${hours}:${minutes}`;
}


// ----------------------------------------------------------------------------------------------------------------

let ongoingGame = false;
let blockArray = [];
let sendInviteArray = [];
let recieveInviteArray = [];
let recipientId;
let allUsers;
let allUsersStatus = {};
let friendList = [];

const chatSections = {};  // Store chat sections for each user

function initializeChatPage() {
  console.log('chat page loaded');
  const token = localStorage.getItem("accessToken");
  const usernamesDiv = document.getElementById('usernames');
  const chatProfileButton = document.getElementById('chat-profile-button');
  const chatInput = document.getElementById('chat-input-container');
  const blockButton = document.getElementById('block-button');
  const friendButton = document.getElementById('friend-button');
  let currentUserName = localStorage.getItem('username');

  let currentUserID = String(jwt_decode(token).user_id);

  // Initial fetch to get all users
  fetch(ip + "auth/user_id_pairs", {
    method: "GET",
    headers: {
        "Content-Type": "application/json",
        "Authorization": "Bearer " + token,
    },
  })
  .then(response => response.json())
  .then(users => {
    console.log("getUserIDPairs:", users);
    allUsers = users;
    allUsers['0'] = 'pong-bot';
    for (let userID in allUsers) {
      let username = allUsers[userID];
      if (currentUserID !== userID) {
        const chatTarget = document.createElement('div');
        addUserToChatList(userID, username, chatTarget);
        // ON CLIICK FOR EACH USER
        handleChatTargetClick(chatTarget, userID);
        usernamesDiv.appendChild(chatTarget);
      }    
    }

    // INITIALIZE BLOCK LIST
    let localblockList = localStorage.getItem(`${currentUserID}.blockList`);
    if (localblockList) {
      blockArray = JSON.parse(localblockList);
      for (let i = 0; i < blockArray.length; i++) {
        const statusIcon = document.getElementById(`status-icon-${blockArray[i]}`);
        const strikethrough = document.getElementById(`chat-target-${blockArray[i]}`).querySelector('p');
        // change status icon to grey if user is blocked
        if (statusIcon && blockArray[i] !== "0") {
          statusIcon.textContent = '⚫';
        }
        strikethrough.style.textDecoration = 'line-through'; // Add a strikethrough 
      }
    }

    // INITIALIZE FRIEND LIST
    let localfriendList = localStorage.getItem(`${currentUserID}.friendList`);
    let userList = document.getElementById('usernames');
    if (localfriendList) {
      friendList = JSON.parse(localfriendList);
      for (let i = 0; i < friendList.length; i++) {
        const statusIcon = document.getElementById(`status-icon-${friendList[i]}`);
        const usertomove = document.getElementById(`chat-target-${friendList[i]}`);
        statusIcon.style.display = '';
        userList.removeChild(usertomove);
        userList.insertBefore(usertomove, userList.children[2])
      }
    }
  });


  // ---------------------------- Block LOGIC ----------------------------
  blockButton.addEventListener('click', function() {
    const indexOfRecipient = blockArray.indexOf(recipientId);
    const statusIcon = document.getElementById(`status-icon-${recipientId}`);
    const strikethrough = document.getElementById(`chat-target-${recipientId}`).querySelector('p');
    if (indexOfRecipient === -1) {
      // User is not blocked, so block them
      blockArray.push(recipientId);
      localStorage.setItem(`${currentUserID}.blockList`, JSON.stringify(blockArray));
      // change button text
      blockButton.textContent = 'Click to Unblock';
      chatProfileButton.textContent = allUsers[recipientId] + ' (BLOCKED)';
      // remove chat input
      chatInput.classList.remove('d-flex');
      chatInput.classList.add('d-none');
      // remove chat section
      chatSections[recipientId].classList.remove('d-flex');
      chatSections[recipientId].classList.add('d-none');
      // change status icon to grey if user is blocked
      if (statusIcon && recipientId !== "0") {
        statusIcon.textContent = '⚫';
      }
      strikethrough.style.textDecoration = 'line-through'; // Add a strikethrough 
    } else {
      // User is blocked, so unblock them
      blockArray.splice(indexOfRecipient, 1);
      localStorage.setItem(`${currentUserID}.blockList`, JSON.stringify(blockArray));
      // change button text
      blockButton.textContent = 'Click to Block';
      chatProfileButton.textContent = allUsers[recipientId];
      // remove chat input
      chatInput.classList.remove('d-none');
      chatInput.classList.add('d-flex');
      // remove chat section
      chatSections[recipientId].classList.remove('d-none');
      chatSections[recipientId].classList.add('d-flex');
      strikethrough.style.textDecoration = 'none'; // Add a strikethrough
    }
  });


  // ---------------------------- FRIEND LOGIC ----------------------------

  friendButton.addEventListener('click', function() {
    let userList = document.getElementById('usernames');
    const indexOfRecipient = friendList.indexOf(recipientId);
    const statusIcon = document.getElementById(`status-icon-${recipientId}`);
    const usertomove = document.getElementById(`chat-target-${recipientId}`);
    
    if (indexOfRecipient === -1) {
      // User is not friend, so add them
      friendList.push(recipientId);
      localStorage.setItem(`${currentUserID}.friendList`, JSON.stringify(friendList));
      friendButton.textContent = 'Unfriend';
      statusIcon.style.display = '';
      userList.removeChild(usertomove);
      userList.insertBefore(usertomove, userList.children[2])
    } else {
      // User is friend, so unfriend them
      friendList.splice(indexOfRecipient, 1);
      localStorage.setItem(`${currentUserID}.friendList`, JSON.stringify(friendList));
      friendButton.textContent = 'Add Friend';
      statusIcon.style.display = 'none';
      userList.removeChild(usertomove);
      userList.appendChild(usertomove);
    }
  });


  // ---------------------------- CHAT PROFILE AND MATCH HISTORY ----------------------------

  const pongGameDiv = document.getElementById('game-container');
  const profileDiv = document.getElementById('profile_settings');
  const profileName = document.getElementById('profile_name');
  const profileEditName = document.getElementById('edit_name');

  chatProfileButton.addEventListener('click', function() {
    if ((profileDiv.style.display === 'none' || profileName.textContent != allUsers[recipientId]) && recipientId !== '0') {
      loadProfile(recipientId);
      profileEditName.style.display = 'none';
    }
    else {
      pongGameDiv.style.display = 'flex'
      profileDiv.style.display = 'none';
      profileEditName.style.display = '';
    }
  });

  // ---------------------------- CHAT SOCKET ----------------------------

  const chatSocket = new WebSocket("wss://" + window.location.host + "/ws/chat/");

  // open socket
  chatSocket.onopen = function (e) {
    // join room with username and also join room with all users
    chatSocket.send(
      JSON.stringify({
        type: "createIndivialRoom",
        userID: currentUserID,
        username: localStorage.getItem('username'),
      })
    );
    // when login, trigger a ping to all users to get online status
    chatSocket.send(
      JSON.stringify({
        type: "getStatusFromAllUsers",
        username: localStorage.getItem('username'),
      })
    );
    console.log("The connection was setup successfully!");
  };

  // close socket
  chatSocket.onclose = function (e) {
    console.error("Chat socket closed unexpectedly", e);
  };

  // Sending message via chat send button
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
    
    // send message
    chatSocket.send(
      JSON.stringify({
        type: "sendDirectMessage",
        message: messageInput,
        recipient_id: recipientId,
        username: allUsers[currentUserID],
      })
    );

    document.querySelector("#id_message_send_input").value = "";
  };


  // ---------------------------- ON MESSAGE RECEIVED ----------------------------

  chatSocket.onmessage = function (e) {
    const data = JSON.parse(e.data);
    console.log("onmessage:", data.purpose, data.senderID, data.senderName, data.message);
    // do not process own messages
    if (data.senderID === currentUserID) {
      return
    }


    // Receive direct message
    if (data.purpose === 'directMessage' && data.senderID && data.senderName && data.message && !blockArray.includes(data.senderID)) {
      
      if (!chatSections[data.senderID]) {
        const chatMessagesDiv = document.createElement('div');
        chatMessagesDiv.className = 'chat-messages flex-grow-1 p-3 overflow-auto d-none';
        chatMessagesDiv.id = `chat-messages-${data.senderID}`;
        chatSections[data.senderID] = chatMessagesDiv;
        document.querySelector('.chat-section').insertBefore(chatMessagesDiv, document.querySelector('.chat-input-container'));
      }
      
      var div = document.createElement("div");
      div.className = "chat-message";
      div.innerHTML = `${data.message}`;

      var timestamp = document.createElement("div");
      timestamp.className = "timestamp";
      timestamp.innerHTML = getTimeStamp(new Date());
      div.appendChild(timestamp);

      chatSections[data.senderID].appendChild(div);
      chatSections[data.senderID].scrollTop = chatSections[data.senderID].scrollHeight;

      const chatTarget = document.getElementById(`chat-target-${data.senderID}`);
      if (chatTarget && !chatTarget.classList.contains('selected')) {
        const unreadCounter = document.getElementById(`unread-counter-${data.senderID}`);
        unreadCounter.textContent = Number(unreadCounter.textContent) + 1;
        unreadCounter.style.display = 'inline';
        console.log('unread message');
      }
    }

    // Receive request for status
    if (data.purpose === 'requestStatus' && data.senderID && data.message && data.senderName && !blockArray.includes(data.senderID)) {

      // New user come online
      if (!allUsers.hasOwnProperty(data.senderID)) {
        allUsers[data.senderID] = data.senderName;
        
        const chatTarget = document.createElement('div');
        addUserToChatList(data.senderID, data.senderName, chatTarget);
        handleChatTargetClick(chatTarget, data.senderID, data.senderName);
        usernamesDiv.appendChild(chatTarget);
        // do a toast if user is new
        showToast(`welcome new user, ${data.senderName}`, 3000);
        const statusIcon = document.getElementById(`status-icon-${data.senderID}`);
        statusIcon.textContent = '🟢';
      }
      else
      {
        const statusIcon = document.getElementById(`status-icon-${data.senderID}`);
        // do a toast if user is online
        if (statusIcon.textContent === '🔴') {
          statusIcon.textContent = '🟢';
          showToast(`${data.senderName} is online`, 3000);
        }
      } 

           
      // update username if other user change username in their profile
      if (data.senderName !== allUsers[data.senderID]) {
        allUsers[data.senderID] = data.senderName;
        const chatTargetElement = document.getElementById(`chat-target-${data.senderID}`);
        chatTargetElement.querySelector('p').textContent = data.senderName;
      }

      // update allUsersStatus in to catch the 2 second deta between ping and statusupdate
      allUsersStatus[data.senderID] = true;
      // response alive to sender
      chatSocket.send(
        JSON.stringify({
          type: "replyPing",
          recipient_id: data.senderID,
          username: allUsers[currentUserID],
        })
      );
    }

    // Receive online status
    if (data.purpose === 'updateStatus' && data.senderID && data.message && !blockArray.includes(data.senderID)) {
      console.log(data.senderID, "is online")

      // change status to green
      const statusIcon = document.getElementById(`status-icon-${data.senderID}`);
      if (statusIcon) {
        statusIcon.textContent = '🟢';
      }
      // update allUsersStatus in to catch the 2 second deta between ping and statusupdate
      allUsersStatus[data.senderID] = true; // Change the status icon to a green circle emoji
    };
    
    // Receieve Invite for game
    if (data.purpose === 'InviteForGame' && data.senderID && data.message && data.senderName && !blockArray.includes(data.senderID)) {
      recieveInviteArray.push(data.senderID);
      if (data.senderID === recipientId) {
        inviteButton.textContent = 'Accept invite';
      }
      showToast(`${data.senderName} invited you to play a game!`, 5000);
    }

    // Recieve Cancel Invite
    if (data.purpose === 'CancelInvite' && data.senderID && data.message && data.senderName && !blockArray.includes(data.senderID)) {
      recieveInviteArray.splice(recieveInviteArray.indexOf(data.senderID), 1);
      if (data.senderID === recipientId) {
        inviteButton.textContent = 'Invite Player to Game';
      }
    }

    // Recieve Accept Invite
    if (data.purpose === 'AcceptInvite' && !ongoingGame && data.senderID && data.message && data.senderName && !blockArray.includes(data.senderID)) {
      showToast(`Pong Game with ${data.senderName}!`, 5000);
      
      const token = localStorage.getItem('accessToken'); // Retrieve the token from localStorage
      if (!token) {
          messageBox.innerText = "You are not logged in.";
          return;
      }
      sendInviteArray.splice(sendInviteArray.indexOf(data.senderID), 1);
      let url = `wss://localhost/ws/game/?token=${encodeURIComponent(token)}&mode=one_on_one&userid=${currentUserID}&opponentid=${data.senderID}`;
      startGame(url);

      inviteButton.style.display = 'none';
      ongoingGame = true;
    }
  };

  // ---------------------------- STATUS UPDATE VIA PINGING ----------------------------

  // ping all users every 5 seconds. reset allUsersStatus Array
  setInterval(() => {
    console.log("pinging all users")
    chatSocket.send(
      JSON.stringify({
        type: "getStatusFromAllUsers",
        content: currentUserID,
        username: allUsers[currentUserID],
      })
    );
  
    // Reset the userReplies dictionary
    allUsersStatus = {};
  }, 5000);

  // check all users status every 7 seconds. 2 second delay from ping all users to get all replies before reflecting latest status
  setInterval(() => {
    // check all users status and update status icon
    for (let ID in allUsers) {
      if (ID != '0' && ID != currentUserID && !allUsersStatus[ID] && !blockArray.includes(ID)) {
        const statusIcon = document.getElementById(`status-icon-${ID}`);
        if (statusIcon) {
          statusIcon.textContent = '🔴';
        }
      }
    }
  }, 7000);


  const inviteButton = document.getElementById('invite-button');

  // ---------------------------- INVITE PLAYER TO GAME ----------------------------

  // on click of invite button
  document.querySelector("#invite-button").onclick = function (e) {
    // error
    if (!recipientId) {
      console.log("No recipient selected");
      return;
    }
    // not allow any invite if game is ongoing or any other condition we want to set.
    if (ongoingGame == true) {
      return;
    }

    
    // SCENARIOS on clicking of invite button

    // First: user accept invite from other user
    if (recieveInviteArray.includes(recipientId)) {
      chatSocket.send(
        JSON.stringify({
          type: "sendInviteInfo",
          message: "AcceptInvite",
          recipient_id: recipientId,
          username: allUsers[currentUserID],
        })
      );
      showToast(`Pong Game with ${allUsers[recipientId]}!`, 5000);
      recieveInviteArray.splice(recieveInviteArray.indexOf(recipientId), 1);
      const token = localStorage.getItem('accessToken'); // Retrieve the token from localStorage
      if (!token) {
          messageBox.innerText = "You are not logged in.";
          return;
      }
      let url = `wss://localhost/ws/game/?token=${encodeURIComponent(token)}&mode=one_on_one&userid=${currentUserID}&opponentid=${recipientId}`;
      startGame(url);

      inviteButton.style.display = 'none';
    }
    // Second: user cancel invite from other users
    else if (sendInviteArray.includes(recipientId)) {
      sendInviteArray.splice(sendInviteArray.indexOf(recipientId), 1);
      inviteButton.textContent = 'Invite Player to Game';
      chatSocket.send(
        JSON.stringify({
          type: "sendInviteInfo",
          message: "CancelInvite",
          recipient_id: recipientId,
          username: allUsers[currentUserID],
        })
      );
    }
    // Third: play with pong-bot
    else if (recipientId === '0') {
      showToast(`Pong Game with pong-bot!`, 5000);
      ongoingGame = true;
      playAI();
      inviteButton.style.display = 'none';
    }
    // Forth: user click to send invite to other user
    else {
      sendInviteArray.push(recipientId);
      inviteButton.textContent = 'Invited. Click to cancel';
      // send system notification
      chatSocket.send(
        JSON.stringify({
          type: "sendSystemMessage",
          message: `You are invited to play a game with ${allUsers[currentUserID]}! Accept the invite at ${allUsers[currentUserID]} chat.`,
          recipient_id: recipientId,
          username: allUsers[currentUserID],
        })
      );
      // send invite info via web socket
      chatSocket.send(
        JSON.stringify({
          type: "sendInviteInfo",
          message: "InviteForGame",
          recipient_id: recipientId,
          username: allUsers[currentUserID],
        })
      );
    }

  };

};
