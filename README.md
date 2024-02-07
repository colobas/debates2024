# Debates das Eleições Legislativas 2024

Este repositório contém código para agregar vídeos e transcrições dos debates das eleições legislativas de 2024.
Em `debates.yaml` vão sendo adicionados os debates à medida que são transmitidos.

O script `process_debates.py` faz o download dos vídeos para obter as transcrições (usando o [whisperx](https://github.com/m-bain/whisperx))
e gera um ficheiro `debates.json` com a informação agregada.

As transcricões obtidas não identificam o nome dos intervenientes - esse passo é feito manualmente.

O site está feito em Svelte e está disponível em [https://debates2024.info](https://debates2024.info).
