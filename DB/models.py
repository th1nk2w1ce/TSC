from sqlalchemy import Column, BigInteger, Integer, String, Boolean
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base

from pathlib import Path

current = Path(__file__).parent.absolute()
db_dir = str(current) + '/'
Path(db_dir).mkdir(parents=True, exist_ok=True)


engine = create_async_engine(
    'sqlite+aiosqlite:///' + db_dir + '/database.db',
    echo=False,
)


async_session = async_sessionmaker(engine)
Base = declarative_base()


#Define users table
class User(Base):
    __tablename__ = 'users'

    tg_id = Column(BigInteger, primary_key=True, unique=True)
    sts = Column(Integer, default='0')
    flag = Column(Integer, default='0')
    referer = Column(BigInteger, default=0)
    all_referals = Column(Integer, default=0)
    referer_address = Column(String, default='0')


async def async_main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
