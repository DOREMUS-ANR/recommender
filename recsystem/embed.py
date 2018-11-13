import common.config as cs
from common.config import config
from embedder import embed

if __name__ == '__main__':
    cs.parse_args()
    embed.main(config)
