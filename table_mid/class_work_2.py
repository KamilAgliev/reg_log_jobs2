from requests import get, post, delete

# delete user
print(delete('http://127.0.0.1:5000/api/v2/users/2').json())
# add user
print(post('http://127.0.0.1:5000/api/v2/users', json={'id': '2',
                                                       'name': 'kama',
                                                       'surname': 'user 2',
                                                       'email': 'kama@f.ru',
                                                       'password': '1232222'
                                                       }, ).json())
# add existing user
print(post('http://127.0.0.1:5000/api/v2/users', json={'id': '2',
                                                       'name': 'kama',
                                                       'surname': 'user 2',
                                                       'email': 'kama@f.ru',
                                                       'password': '1232222'
                                                       }, ).json())
# wrong request
print(post('http://127.0.0.1:5000/api/v2/users', json={'id': '3',
                                                       'email': 'kama@f.ru',
                                                       'password': '1232222'
                                                       }, ).json())
