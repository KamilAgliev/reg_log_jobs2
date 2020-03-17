import sqlalchemy
from sqlalchemy import orm

from data.db_session import SqlAlchemyBase


class HazardCategory(SqlAlchemyBase):
    __tablename__ = 'hazard_category'
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True,
                           autoincrement=True)
    name = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    association_table = sqlalchemy.Table('hazard_association',
                                         SqlAlchemyBase.metadata,
                                         sqlalchemy.Column('jobs',
                                                           sqlalchemy.Integer,
                                                           sqlalchemy.ForeignKey(
                                                               'jobs.id')),
                                         sqlalchemy.Column('hazard_category',
                                                           sqlalchemy.Integer,
                                                           sqlalchemy.ForeignKey(
                                                               'hazard_category.id'))
                                         )
