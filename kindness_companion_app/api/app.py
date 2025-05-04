from flask import Flask

app = Flask(__name__)

# TODO: Register the community_handler blueprint (if implementing the Anonymous Wall API)
# from .community_handler import community_bp
# app.register_blueprint(community_bp, url_prefix='/api/community') # <- 取消此行的注释以启用社区 API

if __name__ == '__main__':
    app.run(debug=True)