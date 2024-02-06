<script>
  import { onMount } from 'svelte';
  import Hls from 'hls.js';
  import ChatDisplay from './ChatDisplay.svelte';

  export let params = {};

  let debateData = {}; // Initialize debateData
  let transcripts = []; // Initialize transcripts
  let subtitlesUrl = `/debates/transcripts/${params.slug}.vtt`;

  // Async function to fetch debate data including video URL and headers
  async function fetchDebateData() {
    const response = await fetch(`/debates/${params.slug}.json`);
    debateData = await response.json();
  }

  // Async function to fetch transcripts
  async function fetchTranscripts() {
    const response = await fetch(`/debates/transcriptions/${params.slug}.json`);
    transcripts = await response.json();
  }

  onMount(async () => {
    await fetchDebateData();
    await fetchTranscripts();

    const video = document.getElementById('video');
    if (Hls.isSupported()) {
      const hls = new Hls({
        xhrSetup: function(xhr, url) {
          // Apply headers from debateData to the request, only if they exist
          if (debateData.headers) {
            Object.keys(debateData.headers).forEach(header => {
              xhr.setRequestHeader(header, debateData.headers[header]);
            });
          }
        }
      });
      hls.loadSource(debateData.m3u8_url);
      hls.attachMedia(video);
    }
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
</style>

<h1>{debateData.title}</h1>

<video id="video" controls>
  <track label="Português" kind="subtitles" srclang="pt" src={subtitlesUrl} default>
</video>

<a href={debateData.original_url} target="_blank">Link para o vídeo original</a>

<ChatDisplay messages={transcripts} />

<a href="/">Voltar à página inicial</a>
