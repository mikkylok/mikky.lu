from flask import render_template, redirect, url_for, flash, request, current_app, abort
from . import main
from ..decorators import admin_required, permission_required
from ..models import User, Permission, Role, Post, Follow, Comment
from flask_login import login_required, current_user, login_required
from .forms import EditProfileForm, EditProfileAdminForm, PostForm, EditPostForm, CommentForm, ChangeAvatarForm
from .. import db
from datetime import datetime
from math import ceil
import logging
import os

@main.route('/', methods=['GET','POST'])
def index():
    current_app.logger.warning('test')
    form = PostForm()
    if current_user.can(Permission.WRITE_ARTICLES) and form.validate_on_submit():
        post = Post(body=form.body.data,
                   # timestamp=datetime.utcnow(),
                   # author_id=current_user.id)
                     author=current_user._get_current_object())
        db.session.add(post)
        #current_user.posts = post
        #db.session.add(current_user)
        flash('You have sent a post successfully.')
        return redirect(url_for('main.index'))
    #posts = Post.query.order_by(db.desc(Post.timestamp)).all()

    page = request.args.get("page",1,type=int)
    pagination = Post.query.order_by(Post.timestamp.desc()).paginate(page,per_page=current_app.config['FLASKY_POSTS_PER_PAGE'],error_out=False)
    posts = pagination.items

    return render_template('index.html', form=form, posts=posts, pagination=pagination, endpoint='main.index')

@main.route('/admin')
@login_required
@admin_required
def for_admins_only():
    #print "for admin"
    return "For administrators!"

@main.route('/moderator')
@login_required
@permission_required(Permission.MODERATE_COMMENTS)
def for_moderators_only():
    return "For comment moderators!"

@main.route('/user/<username>')
def user(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        abort(404)
    #posts = user.posts.order_by(Post.timestamp.desc()).all()

    page = request.args.get("page",1,type=int)
    pagination = user.posts.order_by(Post.timestamp.desc()).paginate(page,per_page=current_app.config['FLASKY_POSTS_PER_PAGE'],error_out=False)
    posts = pagination.items

    return render_template('user.html', user=user, posts=posts, pagination=pagination)

@main.route('/edit-profile', methods=['GET','POST'])
@login_required
def edit_profile():   
    form = EditProfileForm()
    if form.validate_on_submit():
        current_user.name=form.real_name.data
        current_user.location=form.location.data
        current_user.about_me=form.about_me.data
        db.session.add(current_user)
        flash('Your profile has been updated.')
        return redirect(url_for('main.user', username=current_user.username))
    form.real_name.data=current_user.name
    form.location.data=current_user.location
    form.about_me.data=current_user.about_me
    return render_template('edit_profile.html', form=form)

@main.route('/edit-profile/<int:id>',methods=['GET','POST'])
@login_required
@admin_required
def edit_profile_admin(id):
    user = User.query.filter_by(id=id).first()
    if user is None:
        abort(404)        
    form = EditProfileAdminForm(user=user)
    if form.validate_on_submit():
        user.email=form.email.data
        user.username=form.username.data
        user.role=Role.query.get(form.role.data)
        user.name=form.real_name.data
        user.location=form.location.data
        user.about_me=form.about_me.data
        db.session.add(user)
        flash("{}'s profile has been updated.".format(user.username))
        return redirect(url_for('main.user', username=user.username))
    form.email.data=user.email
    form.username.data=user.username
    form.role.data=user.role_id    
    form.real_name.data=user.name
    form.location.data=user.location
    form.about_me.data=user.about_me
    return render_template('edit_profile.html', form=form, user=user)

@main.route('/post/<int:id>', methods=['GET','POST'])
def post(id):
    post = Post.query.get_or_404(id)
    form = CommentForm()
    if current_user.can(Permission.COMMENT) and form.validate_on_submit():
        comment = Comment(body=form.body.data, 
                          author=current_user._get_current_object(),
                          post=post)
        db.session.add(comment)
        flash('Your comment has been published.')
        return redirect(url_for('main.post', id=id,page=-1))
    page = request.args.get("page",1,type=int)
    if page== -1:
        page = ceil(float(post.comments.count())/current_app.config['FLASKY_COMMENTS_PER_PAGE']) 
    pagination = post.comments.order_by(Comment.timestamp.asc()).paginate(page,per_page=current_app.config['FLASKY_COMMENTS_PER_PAGE'],error_out=False)
    comments = pagination.items

    return render_template('post.html', post=post, form=form, comments=comments, pagination=pagination)

@main.route('/edit-post/<int:id>', methods=['GET','POST']) 
@login_required
def edit_post(id):
    post = Post.query.filter_by(id=id).first()
    if post is None:
        abort(404)        
    form = EditPostForm(user=user)
    if current_user.can(Permission.WRITE_ARTICLES) and form.validate_on_submit():
        post.body = form.body.data
        post.timestamp = datetime.utcnow()
        db.session.add(post)
        flash('Your post has been updated.')
        return redirect(url_for('main.post', id=id))
    form.body.data = post.body
    return render_template('edit_post.html', form=form, post=post)

@main.route('/follow/<int:id>')
@login_required
@permission_required(Permission.FOLLOW)
def follow(id):
    user = User.query.filter_by(id=id).first()
    if user is None:
        flash("User doesn't exist.")
        return redirect(url_for('main.index'))
    if current_user.is_following(user):
        flash("You are already following this user.")
        return redirect(url_for('main.user',username=user.username))
    current_user.follow(user)
    flash("You have followed this user.")
    return redirect(url_for('main.user',username=user.username))

@main.route('/unfollow/<int:id>')
@login_required
@permission_required(Permission.FOLLOW)
def unfollow(id):
    user = User.query.filter_by(id=id).first()
    if user is None:
        flash("User doesn't exist.")
        return redirect(url_for('main.index'))
    if not current_user.is_following(user):
        flash("You are already not following this user.")
        return redirect(url_for('main.user',username=user.username))
    current_user.unfollow(user)
    flash("You have unfollowed this user.")
    return redirect(url_for('main.user',username=user.username))

@main.route('/followers/<username>')
def followers(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash("User doesn't exist.")
        return redirect(url_for('main.index'))
    page = request.args.get("page",1,type=int)
    pagination = user.followers.order_by(Follow.timestamp.desc()).paginate(page,per_page=current_app.config['FLASKY_FOLLOWERS_PER_PAGE'],error_out=False)
    followers = [{"user":item.follower,"timestamp":item.timestamp} for item in pagination.items] 
    return render_template('followers.html', people=followers, user=user, pagination=pagination, title="Followers", endpoint="main.followers")

@main.route('/following/<username>')
def following(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash("User doesn't exist.")
        return redirect(url_for('main.index'))
    page = request.args.get("page",1,type=int)
    pagination = user.followed.order_by(Follow.timestamp.desc()).paginate(page,per_page=current_app.config['FLASKY_FOLLOWERS_PER_PAGE'],error_out=False)
    following = [{"user":item.followed,"timestamp":item.timestamp} for item in pagination.items] 
    return render_template('followers.html', people=following, user=user, pagination=pagination, title="Following", endpoint="main.following")

@main.route('/index_following')
@login_required
def index_following():
    form = PostForm()
    if current_user.can(Permission.WRITE_ARTICLES) and form.validate_on_submit():
        post = Post(body=form.body.data, author=current_user._get_current_object())
        db.session.add(post)
        flash('You have sent a post successfully.')
        return redirect(url_for('main.index'))
    page = request.args.get("page",1,type=int)
    pagination = current_user.followed_posts.order_by(Post.timestamp.desc()).paginate(page,per_page=current_app.config['FLASKY_POSTS_PER_PAGE'],error_out=False)
    posts = pagination.items
    return render_template('index.html', form=form, posts=posts, pagination=pagination, endpoint='main.index_following')

@main.route('/delete-comment/<int:id>')
@login_required
def delete_comment(id):
    comment = Comment.query.get_or_404(id)
    if current_user==comment.author:
        db.session.delete(comment)
        flash('Your comment has been deleted.')
        return redirect(url_for('main.post', id=comment.post_id))

@main.route('/moderate-comments')
@login_required
@permission_required(Permission.MODERATE_COMMENTS)
def moderate_comments():
    page = request.args.get('page',1,type=int) 
    current_app.logger.warning('moderate get page:{}'.format(page))    
    pagination = Comment.query.order_by(Comment.timestamp.desc()).paginate(page,per_page=current_app.config['FLASKY_COMMENTS_PER_PAGE'],error_out=False)
    comments = pagination.items
    return render_template('moderate_comments.html', comments=comments, pagination=pagination, page=page)

@main.route('/moderate-comments/disable/<int:id>')
@login_required
@permission_required(Permission.MODERATE_COMMENTS)
def disable(id): 
    #current_app.logger.warning('disable get page:{}'.format(page))    
    comment = Comment.query.get_or_404(id)
    comment.disabled = True
    db.session.add(comment)
    return redirect(url_for('main.moderate_comments', page=request.args.get('page',1,type=int)))

@main.route('/moderate-comments/enable/<int:id>')
@login_required
@permission_required(Permission.MODERATE_COMMENTS)
def enable(id):
    comment = Comment.query.get_or_404(id)
    comment.disabled = False
    db.session.add(comment)
    return redirect(url_for('main.moderate_comments', page=request.args.get("page",1,type=int)))


@main.route('/change-avatar/<username>', methods=['GET','POST'])
@login_required
def change_avatar(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        abort(404)
    form = ChangeAvatarForm()
    if form.validate_on_submit():
        avatar = request.files['avatar']
        filename = avatar.filename
        UPLOAD_FOLDER = current_app.config['UPLOAD_FOLDER']
        path='{}{}_{}'.format(UPLOAD_FOLDER,user.username,filename)
        avatar.save(path)
        size = os.stat(path).st_size
        if size <= 1024*1024:
            user.profile_picture = '/static/avatar/{}_{}'.format(user.username,filename)
            db.session.add(user)
            flash("You have updated your profile picture.")
        else:
            flash("Size should be less than 1MB.Please upload again!")
        return redirect(url_for('main.change_avatar', username=user.username))
    return render_template('change_avatar.html', form=form, user=user)

@main.route('/resume')
def resume():
    return render_template('resume.html')
