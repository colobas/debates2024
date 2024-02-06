<script>
  import debates from './debates.json';
</script>

<style>
  .grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
    gap: 16px;
    padding: 20px;
  }
  .debate {
    cursor: pointer;
  }
  img {
    width: 100%;
    height: auto;
    border-radius: 8px;
  }
</style>

<h1>Debates Legislativas 2024</h1>

Aqui pode encontrar os vídeos dos debates para as eleições legislativas de 2024,
bem como as respectivas transcrições (obtidas automáticamente, e por isso sujeitas a erros.

Clique num vídeo para ver o debate completo.

<div class="grid">
  {#each debates as { title, thumbnail, slug }}
    <div class="debate" on:click={() => (window.location.href = `/#/debate/${slug}`)}>
      <img src={thumbnail} alt={title} />
      <p>{title}</p>
    </div>
  {/each}
</div>
