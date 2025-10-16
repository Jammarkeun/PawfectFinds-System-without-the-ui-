from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from app.models.user import User
from app.utils.decorators import anonymous_required, login_required
from app.forms import LoginForm, SignupForm, PasswordResetRequestForm, PasswordResetForm, ChangePasswordForm
import secrets
import hashlib
from datetime import datetime, timedelta

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
@anonymous_required
def login():
    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data.strip()
        password = form.password.data
        
        user = User.authenticate(email, password)
        if user:
            if user['status'] != 'active':
                flash('Your account has been deactivated. Please contact support.', 'error')
                return render_template('auth/login.html', form=form)
            
            session['user_id'] = user['id']
            session['user_role'] = user['role']
            session.permanent = True
            
            # Redirect based on role
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            
            if user['role'] == 'admin':
                return redirect(url_for('admin.dashboard'))
            elif user['role'] == 'seller':
                return redirect(url_for('seller.dashboard'))
            elif user['role'] == 'rider':
                return redirect(url_for('rider.dashboard'))
            else:
                return redirect(url_for('public.browse_products'))
        else:
            flash('Invalid email or password.', 'error')
    
    return render_template('auth/login.html', form=form)

@auth_bp.route('/signup', methods=['GET', 'POST'])
@anonymous_required
def signup():
    form = SignupForm()
    if form.validate_on_submit():
        username = form.username.data.strip()
        email = form.email.data.strip()
        password = form.password.data
        first_name = form.first_name.data.strip()
        last_name = form.last_name.data.strip()
        phone = form.phone.data.strip() if form.phone.data else None
        address = form.address.data.strip() if form.address.data else None
        
        # Check if user exists
        if User.get_by_email(email):
            flash('An account with this email already exists.', 'error')
            return render_template('auth/signup.html', form=form)
        
        if User.get_by_username(username):
            flash('This username is already taken.', 'error')
            return render_template('auth/signup.html', form=form)
        
        # Create user
        user = User.create(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            phone=phone,
            address=address
        )
        
        if user:
            flash('Account created successfully! Please log in.', 'success')
            return redirect(url_for('auth.login'))
        else:
            flash('Failed to create account. Please try again.', 'error')
    
    return render_template('auth/signup.html', form=form)

@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('public.landing'))

@auth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """User profile management"""
    user = User.get_by_id(session['user_id'])
    if not user:
        flash('User not found.', 'error')
        return redirect(url_for('auth.login'))
    
    if request.method == 'POST':
        # Update profile
        update_data = {
            'first_name': request.form.get('first_name', '').strip(),
            'last_name': request.form.get('last_name', '').strip(),
            'phone': request.form.get('phone', '').strip(),
            'address': request.form.get('address', '').strip()
        }
        
        # Remove empty values
        update_data = {k: v for k, v in update_data.items() if v}
        
        if User.update(session['user_id'], **update_data):
            flash('Profile updated successfully!', 'success')
        else:
            flash('Failed to update profile.', 'error')
        
        return redirect(url_for('auth.profile'))
    
    return render_template('auth/profile.html', user=user)

@auth_bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    """Change user password"""
    form = ChangePasswordForm()
    if form.validate_on_submit():
        user = User.get_by_id(session['user_id'])
        if not user:
            flash('User not found.', 'error')
            return redirect(url_for('auth.login'))
        
        # Verify current password
        if not User.authenticate(user['email'], form.current_password.data):
            flash('Current password is incorrect.', 'error')
            return render_template('auth/change_password.html', form=form)
        
        # Update password
        if User.update_password(session['user_id'], form.new_password.data):
            flash('Password changed successfully!', 'success')
            return redirect(url_for('auth.profile'))
        else:
            flash('Failed to change password.', 'error')
    
    return render_template('auth/change_password.html', form=form)

@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
@anonymous_required
def forgot_password():
    """Password reset request"""
    form = PasswordResetRequestForm()
    if form.validate_on_submit():
        email = form.email.data.strip()
        user = User.get_by_email(email)
        
        if user:
            # Generate reset token
            token = secrets.token_urlsafe(32)
            token_hash = hashlib.sha256(token.encode()).hexdigest()
            
            # Store token in database (you might want to create a separate table for this)
            # For now, we'll use a simple approach
            session[f'reset_token_{user["id"]}'] = {
                'token_hash': token_hash,
                'expires': (datetime.now() + timedelta(hours=1)).isoformat()
            }
            
            # In a real application, you'd send an email here
            flash(f'Password reset instructions have been sent to {email}. Reset link (for demo): /auth/reset-password/{user["id"]}/{token}', 'info')
        else:
            # Don't reveal whether email exists or not
            flash(f'If an account with {email} exists, password reset instructions have been sent.', 'info')
        
        return redirect(url_for('auth.login'))
    
    return render_template('auth/forgot_password.html', form=form)

@auth_bp.route('/reset-password/<int:user_id>/<token>', methods=['GET', 'POST'])
@anonymous_required
def reset_password(user_id, token):
    """Password reset form"""
    # Verify token
    session_key = f'reset_token_{user_id}'
    if session_key not in session:
        flash('Invalid or expired reset token.', 'error')
        return redirect(url_for('auth.forgot_password'))
    
    token_data = session[session_key]
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    
    if (token_hash != token_data['token_hash'] or 
        datetime.now() > datetime.fromisoformat(token_data['expires'])):
        flash('Invalid or expired reset token.', 'error')
        return redirect(url_for('auth.forgot_password'))
    
    form = PasswordResetForm()
    if form.validate_on_submit():
        if User.update_password(user_id, form.password.data):
            # Clear the reset token
            session.pop(session_key, None)
            flash('Password reset successfully! Please log in with your new password.', 'success')
            return redirect(url_for('auth.login'))
        else:
            flash('Failed to reset password.', 'error')
    
    return render_template('auth/reset_password.html', form=form)
