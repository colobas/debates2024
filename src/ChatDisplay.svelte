<script>
  export let messages = []; // Expects an array of { speaker, text }

  let speakerSide = "right"; // Default side for the first speaker

  // A function to determine if the speaker changes between messages
  const getSpeakerSide = (index) => {
     if (index === 0){ return speakerSide };
     if (messages[index].speaker !== messages[index - 1].speaker) {
       speakerSide = speakerSide === "right" ? "left" : "right";
     }
     return speakerSide;
  };

  // Generating a unique color for each speaker
  const speakerColors = {};
  messages.forEach((msg) => {
    if (!speakerColors[msg.speaker]) {
      speakerColors[msg.speaker] = `hsl(${Math.floor(Math.random() * 360)}, 70%, 60%)`;
    }
  });
</script>

<style>
  .chat-container {
    display: flex;
    width: 80%;
    margin: auto;
    flex-direction: column;
  }
  .message {
    padding: 10px;
    border-radius: 20px;
    margin: 5px;
    max-width: 60%;
  }
  .left {
    align-self: flex-start;
  }
  .right {
    align-self: flex-end;
  }
</style>

<div class="chat-container">
  {#each messages as { speaker, text }, index}
    <div class="message {getSpeakerSide(index)}"
         style="background-color: {speakerColors[speaker]};">
      <strong>{speaker}:</strong> {text}
    </div>
  {/each}
</div>
