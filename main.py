from logger import setup_logging
setup_logging()

from config import TOKEN
from telegram.ext import Application, JobQueue
from handlers.user_commands_handlers import user_commands_handlers
from handlers.interaction_handlers import interaction_handlers
import logging

logger = logging.getLogger(__name__)

def main():
  app = Application.builder().token(TOKEN).job_queue(JobQueue()).build()

  add_handlers(app)
  logger.info("Bot started")
  app.run_polling()

def add_handlers(app: Application):
  for handler in user_commands_handlers:
    app.add_handler(handler)
  for handler in interaction_handlers:
    app.add_handler(handler)

if __name__ == "__main__":
  main()