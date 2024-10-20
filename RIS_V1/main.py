import uvicorn
import sys
from config import config


if __name__ == '__main__':
        try:
                uvicorn.run("app.fastapi:app",
                        host = config.HOST,
                        port = config.PORT,
                        reload = config.RELOAD
                        # workers = config.WORKERS,
                        # limit_concurrency = config.LIMIT_CONCURRENCY
                        )
                
        except Exception as e:
                print(e)
        
