import firebase_admin
from pprint import pprint
from firebase_admin import credentials
from firebase_admin import auth
from firebase_admin import firestore

cred = credentials.Certificate("./firebase_serviceAccount.json")
firebase_admin.initialize_app(cred)

firestore_client = firestore.client()

def createStudentAccount(name, email_id, password="pass@123"):
    user = auth.create_user(
        display_name=name,
        email=email_id,
        email_verified=True,
        password=password
    )
    firestore_client.collection('users').document(user.uid).set({
        'name': name,
        'email': email_id,
        'image': None,
        'uid': user.uid,
        'token': None,
        'locale': 'en',
        'updatedGroups': [],
        'joinedGroups': [],
        'status': ""
    })
    print("Created user", user.uid)
    return user.uid
    

def createGroup(group_name, abbreviation, color, members, college_id):

    # Step 1: Create a blank group with participants

    _, groupRef = firestore_client.collection('groups').add({
        'abbreviation': abbreviation,
        'name': group_name,
        'color': color,
        'members': members,
        'collegeid': college_id
    })

    print(type(groupRef))
    print(groupRef)

    # Step 2: Create a general channel
    firestore_client.collection('groups').document(groupRef.id).collection('channels').add({
            'name': 'General',
            'type': 'TOPIC',
            'visibility': 'OPEN'
        })
    
    # Step 3: Update users who are added
    for member in members:
        member_data = firestore_client.collection('users').document(member).get().to_dict()
        joinedGroups = member_data['joinedGroups']
        joinedGroups.append(groupRef.id)
        member_data['joinedGroups'] = joinedGroups
        firestore_client.collection('users').document(member).set(member_data)

    print("Created group", groupRef.id)


def createPrivateChannel(group_id, channel_name):
    # use this in conjunction with `add_user_to_channel` 
    _, channelRef = firestore_client.collection('groups').document(group_id).collection('channels').add({
        'name': channel_name,
        'type': 'TOPIC',
        'visibility': 'CLOSED'
    })
    print("Created channel", channelRef.id)
    return channelRef.id


def get_group_data(group_id):
    # get_group_data(group_id).to_dict() will give data of group
    # get_group_data(group_id).id will give ID of the group
    return firestore_client.collection('groups').document(group_id).get()

def get_channel_data(group_id, channel_id):
    # get_group_data(group_id).to_dict() will give data of group
    # get_group_data(group_id).id will give ID of the group
    return firestore_client.collection('groups').document(group_id).collection('channels').document(channel_id).get()


def get_member_data_from_group(group_id):
    group_data = firestore_client.collection('groups').document(group_id).get().to_dict()
    members = group_data['members']
    
    def f(member):
        return firestore_client.collection('users').document(member).get().to_dict()

    all_member_data = list(map(f, members))
    print(all_member_data)
    return all_member_data

# def get_channel_members(group_id, channel_id):
#     return firestore_client.collection('groups').document(group_id)


def college_login(username, password):
    user = firestore_client.collection('colleges').where('username', '==', username).get()
    if user is None:
        return None, None
    else:
        user_data = None
        for i in user:
            user_data = i.to_dict()
        if user_data:
            if password == user_data['password']:
                return True, i.id
            else:
                return None, None
        return None, None


def get_member_data_from_channel(group_id, channel_id):
    users = firestore_client.collection('groups').document(group_id).collection('channels').document(channel_id).collection('users').get()
    uids = []

    for user in users:
        uids.append(user.id)
    
    def f(member):
        return firestore_client.collection('users').document(member).get().to_dict()

    all_member_data = list(map(f, uids))
    return all_member_data

def add_user_to_group(group_id, user_uid):
    # Update group members
    group = firestore_client.collection('groups').document(group_id).get().to_dict()
    group_members = group['members']
    group_members.append(user_uid)
    group['members'] = group_members
    firestore_client.collection('groups').document(group_id).set(group)

    # Update group id in users
    member_data = firestore_client.collection('users').document(user_uid).get().to_dict()
    joinedGroups = member_data['joinedGroups']
    joinedGroups.append(group_id)
    member_data['joinedGroups'] = joinedGroups
    firestore_client.collection('users').document(user_uid).set(member_data)


def add_user_to_channel(group_id, channel_id, user_uid):
    firestore_client.collection('groups').document(group_id).collection('channels').document(channel_id).collection('users').document(user_uid).set({
        'hasUpdates': False,
        'invitation': True,
        'rsvp': "UNSET",
        'uid': user_uid
    })

def get_user_data(user_uid):
    return firestore_client.collection('users').document(user_uid).get().to_dict()

def get_groups_by_college(college_id):
    return firestore_client.collection('groups').where('collegeid', '==', college_id).get()

def get_all_groups():
    return firestore_client.collection('groups').get()

def get_channels_from_group(group_id):
    return firestore_client.collection('groups').document(group_id).collection('channels').get()

def createCollegeAccount(college_name, username, password="pass@123"):
    _, college = firestore_client.collection('colleges').add({
        'name': college_name,
        'username': username,
        'password': password
    })
    print("Created college", college.id)


def createFacultyAccount(name, email_id, college_id, password="pass@123"):
    user = auth.create_user(
        display_name=name,
        email=email_id,
        email_verified=True,
        password=password
    )
    firestore_client.collection('users').document(user.uid).set({
        'name': name,
        'email': email_id,
        'image': None,
        'uid': user.uid,
        'token': None,
        'locale': 'en',
        'updatedGroups': [],
        'joinedGroups': [],
        'status': ""
    })

    firestore_client.collection('colleges').document(college_id).collection('teachers').document(user.uid).set({
        'name': name,
        'email_id': email_id
    })

    print("Created faculty", user.uid)
    return user.uid


def getFacultiesFromCollege(college_id):
    return firestore_client.collection('colleges').document(college_id).collection('teachers').get()


def checkIfUserIsInGroup(user_uid, group_id):
    group_data = firestore_client.collection('groups').document(group_id).get().to_dict()
    members = group_data['members']
    if user_uid in members:
        return True
    else:
        return False

# checkIfUserIsInGroup("joZ2lFpAHrYIkq7saDgE7fyDa6R2", "p7C38FC7plSN2Cucpmdj")

# createCollegeAccount("NMIMS", "nmims_admin")
# createFacultyAccount("Vaishali Kulkarni", "vku@nmims.edu", "nI0YgLsFnP49zRQrvMaP")

"""
teachers = getFacultiesFromCollege("nI0YgLsFnP49zRQrvMaP")
for teacher in teachers:
    print(teacher.id)
    print(teacher.to_dict())
"""

# createGroup("B.Tech Mechatronics", "MX", "eeeeee", ["joZ2lFpAHrYIkq7saDgE7fyDa6R2"])
# get_user_data("joZ2lFpAHrYIkq7saDgE7fyDa6R2")
# createStudentAccount("Name", "email_id")

"""
To get all groups 
----------------------------
groups = get_all_groups()
for group in groups:
    print(group.id) ---- for getting group ID
    pprint(group.to_dict())
"""

# get_member_data_from_group("T8hujIF2vNb4KO0dywXd")

# add_user_to_group("p7C38FC7plSN2Cucpmdj", "joZ2lFpAHrYIkq7saDgE7fyDa6R2")
# add_user_to_channel("p7C38FC7plSN2Cucpmdj", "xYofiPRakZNuPxljM7BO", "joZ2lFpAHrYIkq7saDgE7fyDa6R2")
# get_group_data("p7C38FC7plSN2Cucpmdj")