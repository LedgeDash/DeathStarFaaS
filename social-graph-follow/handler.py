def handle(req):
    """Add followee_id into the followee list of user_id and add user_id into
    the follower list of the followee_id in the social_graph database
    Args:
        req (str): request body
        
        user_id
        followee_id
    """

    if ('user_id' not in payload or
       'followee_id' not in payload):
        sys.exit('Error: missing input. Make sure the input has `user_id` and `followee_id` fields')

    

    return req
