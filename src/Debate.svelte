<script>
  import { onMount } from 'svelte';
  import Hls from 'hls.js';

  export let params = {};

  let debateData = {}; // Initialize debateData
  let transcripts = []; // Initialize transcripts
  let speakerColors = {}; // Initialize speakerColors

  // Async function to fetch debate data including video URL and headers
  async function fetchDebateData() {
    const response = await fetch(`/debates/${params.slug}.json`);
    debateData = await response.json();
  }

  // Function to generate colors for each speaker
  function generateSpeakerColors() {
    transcripts.forEach((msg) => {
      if (!speakerColors[msg.speaker]) { // Check if the speaker already has a color
        speakerColors[msg.speaker] = `hsl(${Math.floor(Math.random() * 360)}, 70%, 60%)`;
      }
    });
  }

  // Async function to fetch transcripts
  async function fetchTranscripts() {
    const response = await fetch(`/debates/transcriptions/${params.slug}.json`);
    transcripts = await response.json();
    generateSpeakerColors();
  }
    
  // Async function to assemble video
  async function assembleVideo() {
    const video = document.getElementById('video');
    if (Hls.isSupported()) {
      const hls = new Hls();
      hls.loadSource(`/debates/hls/${params.slug}.m3u8`);
      hls.attachMedia(video);
    } else {
      video.src = `/debates/hls/${params.slug}.m3u8`;
    }

    const chatContainer = document.querySelector('.chat-container');

    video.addEventListener('timeupdate', () => {
      if (!chatContainer) return;
      const currentTime = video.currentTime;
      let lastPastMessageIndex = transcripts.findIndex((transcript, index) => {
        return index < transcripts.length - 1 && transcripts[index + 1].time > currentTime;
      });

      if (lastPastMessageIndex === -1) {
        lastPastMessageIndex = transcripts.length - 1; // If no future message, use the last one
      }

      const messageElements = chatContainer.querySelectorAll('.message');
      const currentMessageElement = messageElements[lastPastMessageIndex];

      // if video is playing, auto scroll to the current message
      if (currentMessageElement && !video.paused) {
        chatContainer.scrollTop = currentMessageElement.offsetTop - chatContainer.offsetTop - 20; // Adjust 20px offset if needed
      }
    });
  }

  // A function to determine if the speaker changes between transcripts
  const getSpeakerSide = (index) => {
     if (index === 0){ return speakerSide };
     if (transcripts[index].speaker !== transcripts[index - 1].speaker) {
       speakerSide = speakerSide === "right" ? "left" : "right";
     }
     return speakerSide;
  };

  // Default side for the first speaker
  let speakerSide = "right";
 
  const setVideoTime = (time) => {
    document.getElementById('video').currentTime = parseFloat(time);
  };

  onMount(async () => {
    await fetchDebateData();
    await assembleVideo();

    transcripts.forEach((msg) => {
      speakerColors[msg.speaker] = `hsl(${Math.floor(Math.random() * 360)}, 70%, 60%)`;
    });
  });
</script>

<style>
  h1 {
    text-align: center;
  }
  video {
    width: 50%;
    margin: 0 auto;
    display: block;
  }
  a {
    display: block;
    text-align: center;
    margin-top: 20px;
  }
  .chat-container {
    display: flex;
    width: 80%;
    margin: auto;
    flex-direction: column;
    max-height: 400px; /* Limit the height of the chat container */
    overflow-y: auto; /* Enable vertical scrolling */
  }
  .message {
    padding: 10px;
    border-radius: 20px;
    margin: 5px;
    max-width: 60%;
    cursor: pointer;
  }
  .left {
    align-self: flex-start;
  }
  .right {
    align-self: flex-end;
  }

</style>

<h1>{debateData.title}</h1>

<video id="video" controls>
</video>


{#await fetchTranscripts()}
{:then}
  <div class="chat-container">
    {#each transcripts as { speaker, text, time}, index}
      <div class="message {getSpeakerSide(index)}" href="javascript:void(0)" style="background-color:{speakerColors[speaker]};"
           on:click={() => setVideoTime(time)}>
        <strong>{speaker}:</strong> {text}
      </div>
    {/each}
  </div>
{:catch}
  <p>Erro ao carregar transcrições</p>
{/await}

<a href="/">Voltar à página inicial</a>
<a href={debateData.original_url} target="_blank">Link para o vídeo original</a>
