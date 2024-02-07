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
bem como as respectivas transcrições <strong>(obtidas
<a href="https://github.com/colobas/debates2024/blob/9d735da1b7c3542fb34d80c8ef7d35a61e2d0d3d/process_debates.py#L146-L176">automaticamente</a>,
e por isso sujeitas a erros).</strong>

Clique num vídeo para ver o debate completo.

<div class="grid">
  {#each debates as { title, thumbnail, slug }}
    <div class="debate" on:click={() => (window.location.href = `/#/debate/${slug}`)}>
      <img src={thumbnail} alt={title} />
      <p>{title}</p>
    </div>
  {/each}
</div>
