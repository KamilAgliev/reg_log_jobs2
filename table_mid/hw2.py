from requests import delete, post

# add
print(post('http://127.0.0.1:5000/api/v2/jobs', json={'id': 3,
                                                      'job': 'some job',
                                                      'team_leader': 1,
                                                      'work_size': 22,
                                                      'collaborators': '1,2,3',
                                                      'start_date': 'now',
                                                      'end_date': 'tomorrow',
                                                      'is_finished': True,
                                                      'creator': 1
                                                      }, ).json())
# post with missing arguments
print(post('http://127.0.0.1:5000/api/v2/jobs', json={
    'team_leader': 1,
    'work_size': 22,
    'collaborators': '1,2,3',
    'start_date': 'now',
    'end_date': 'tomorrow',
    'is_finished': True,
    'creator': 1
}, ).json())

# deleting
print(delete('http://127.0.0.1:5000/api/v2/jobs/3').json())

# deleting not existing job
print(delete('http://127.0.0.1:5000/api/v2/jobs/3').json())