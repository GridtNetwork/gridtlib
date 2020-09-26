import random
from .helpers import session_scope, possible_leaders
from models.movement import Movement, User, Signal, MovementUserAssociation




class LeaderResource(Resource):
    @jwt_required()
    def post(self, movement_id, leader_id):
        movement = get_movement(movement_id)

        if not current_identity in movement.current_users:
            return {"message": "User is not subscribed to this movement."}, 400

        leader = get_user(leader_id)

        # This prevents a malicious user from finding user ids.
        # Returning a 404 for a nonexistant user would give them more
        # infromation than we want to share.
        if not leader or leader not in current_identity.leaders(movement):
            return {"message": "User is not following this leader."}, 400

        new_leader = movement.swap_leader(current_identity, leader)

        if not new_leader:
            return {"message": "Could not find leader to replace the current one."}

        time_stamp = None
        if Signal.find_last(new_leader, movement):
            time_stamp = str(Signal.find_last(new_leader, movement).time_stamp)

        leader_dict = new_leader.dictify()
        leader_dict["last_signal"] = time_stamp

        return (
            leader_dict,
            200,
        )
