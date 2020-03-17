import flask
from flask import jsonify, request

from data import db_session
from data.jobs import Jobs

blueprint = flask.Blueprint('jobs_api', __name__,
                            template_folder='templates')


@blueprint.route('/api/jobs')
def get_jobs():
    session = db_session.create_session()
    jobs = session.query(Jobs).all()
    return jsonify(
        {
            'jobs':
                [item.to_dict(
                    only=('id', 'user.name', 'job', 'team_leader', 'work_size',
                          'collaborators', 'start_date', 'end_date',
                          'is_finished', 'creator'))
                    for item in jobs]
        }
    )


@blueprint.route('/api/jobs/<int:job_id>')
def get_job(job_id):
    session = db_session.create_session()
    job = session.query(Jobs).filter(Jobs.id == job_id).first()
    if not job:
        return jsonify({'error': 'Not found'})
    return jsonify(
        {
            'jobs':
                job.to_dict(
                    only=('id', 'user.name', 'job', 'team_leader', 'work_size',
                          'collaborators', 'start_date', 'end_date',
                          'is_finished', 'creator'))
        }
    )


@blueprint.route('/api/jobs', methods=['POST'])
def create_job():
    if not request.json:
        return jsonify({'error': 'Empty request'})
    elif not all(key in request.json for key in
                 ['id', 'team_leader', 'job', 'work_size', 'collaborators',
                  'start_date', 'end_date', 'is_finished', 'creator']):
        return jsonify({'error': 'Bad request'})
    session = db_session.create_session()
    exist = session.query(Jobs).filter(Jobs.id == request.json['id']).first()
    if exist:
        return jsonify({'error': 'Id already exists'})
    job = Jobs(
        id=request.json['id'],
        team_leader=request.json['team_leader'],
        job=request.json['job'],
        work_size=request.json['work_size'],
        collaborators=request.json['collaborators'],
        start_date=request.json['start_date'],
        end_date=request.json['end_date'],
        is_finished=request.json['is_finished'],
        creator=request.json['creator']
    )
    session.add(job)
    session.commit()
    return jsonify({'success': 'OK'})
