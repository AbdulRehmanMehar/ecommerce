import os
from .. import app
from flask import abort, flash, Blueprint, render_template, request, redirect, url_for
from flask_login import current_user
from ..forms import AddCategoryForm, UpdateCategoryForm, AddProductForm, UpdateProductForm, PhotoUploadForm
from ..models import db, Category, Product
from ..utils import Pagination

admin = Blueprint('admin', __name__)


@admin.before_request
def restrict():
    if not current_user.is_authenticated:
        return abort(403)
    if not current_user.admin:
        flash('It seems you\'re not admin.', 'danger')
        return abort(403)


@admin.route('/')
def home():
    return render_template('admin/home.html')


# Category Routes


@admin.route('/category')
def category():
    return render_template('admin/category/home.html')


@admin.route('/category/add', methods=['GET', 'POST'])
def add_category():
    form = AddCategoryForm(request.form)
    if request.method == 'POST' and form.validate():
        parent = Category.query.filter(Category.name == str(form.parent.data)).first()
        cat = Category(form.name.data, parent.id if parent else None)
        db.session.add(cat)
        db.session.commit()
        return redirect(url_for('admin.view_categories'))

    return render_template('admin/category/add.html', form=form)


@admin.route('/category/delete/<int:id>')
def delete_category(id):
    cat = Category.query.filter(Category.id == id).first()
    db.session.delete(cat)
    db.session.commit()
    return redirect(url_for('admin.view_categories'))


@admin.route('/category/edit/<int:id>', methods=['GET', 'POST'])
def update_category(id):
    cat = Category.query.filter(Category.id == id).first()
    form = UpdateCategoryForm(cat, request.form)
    if request.method == 'GET':
        form.set_defaults()
    if request.method == 'POST' and form.validate():
        cat = Category.query.filter(Category.id == id).first()
        parent = Category.query.filter(Category.name == str(form.parent.data)).first()
        cat.name = form.name.data
        print(form.name.data)
        cat.parent_id = parent.id if parent else None
        db.session.commit()
        return redirect(url_for('admin.view_categories'))
    return render_template('admin/category/edit.html', form=form, cat_id=cat.id)


@admin.route('/category/view', defaults={'page': 1})
@admin.route('/category/view/<int:page>')
def view_categories(page):
    paginator = Pagination(Category, 10, page)
    return render_template('admin/category/view.html',
                           pages=paginator.pages,
                           categories=paginator.get_results(),
                           items_per_page=paginator.get_items_per_page(),
                           current_page_number=paginator.get_current_page_number()
                           )


# Product Routes


@admin.route('/product')
def product():
    return render_template('admin/product/home.html')


@admin.route('/product/add', methods=['GET', 'POST'])
def add_product():
    form = AddProductForm(request.form)
    photo_form = PhotoUploadForm(request.files)
    if request.method == 'POST' and form.validate() and photo_form.validate():
        cat = Category.query.filter(Category.name == str(form.category.data)).first()
        file = f'{form.title.data}.{photo_form.ext}'
        prod = Product(form.title.data, form.price.data, form.description.data, file, cat.id)
        photo = request.files[photo_form.photo.name]
        photo.save(os.path.join(f'{app.config["UPLOADS_FOLDER"]}/products', file))
        db.session.add(prod)
        db.session.commit()
        return redirect(url_for('admin.view_products'))

    return render_template('admin/product/add.html', form=form, photo_form=photo_form)


@admin.route('/product/delete/<int:id>')
def delete_product(id):
    prod = Product.query.filter(Product.id == id).first()
    db.session.delete(prod)
    db.session.commit()
    return redirect(url_for('admin.view_products'))


@admin.route('/product/edit/<int:id>', methods=['GET', 'POST'])
def update_product(id):
    prod = Product.query.get(id)
    form = UpdateProductForm(request.form)
    photo_form = PhotoUploadForm(request.files)
    if request.method == 'GET':
        form.set_default(prod)
    if request.method == 'POST' and form.validate():
        file = prod.photo
        if photo_form.photo.data:
            if not photo_form.validate():
                return render_template('admin/product/edit.html', p_id=prod.id, form=form, photo_form=photo_form)
            file = f'{form.title.data}.{photo_form.ext}'
            photo = request.files[photo_form.photo.name]
            os.remove(os.path.join(f'{app.config["UPLOADS_FOLDER"]}/products', prod.photo))
            photo.save(os.path.join(f'{app.config["UPLOADS_FOLDER"]}/products', file))
        cat = Category.query.filter(Category.name == str(form.category.data)).first()
        prod.title = form.title.data
        prod.price = form.price.data
        prod.category_id = cat.id
        prod.photo = file
        prod.description = form.description.data
        db.session.commit()
        return redirect(url_for('admin.view_products'))

    return render_template('admin/product/edit.html', p_id=prod.id, form=form, photo_form=photo_form)


@admin.route('/product/view', defaults={'page': 1})
@admin.route('/product/view/<int:page>')
def view_products(page):
    paginator = Pagination(Product, 10, page)
    return render_template('admin/product/view.html',
                           pages=paginator.pages,
                           products=paginator.get_results(),
                           items_per_page=paginator.get_items_per_page(),
                           current_page_number=paginator.get_current_page_number()
                           )