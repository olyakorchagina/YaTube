from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render

from posts.forms import CommentForm, PostForm
from posts.models import Follow, Group, Post, User

POSTS_ON_PAGE = 10


def index(request):
    post_list = Post.objects.select_related('group', 'author')
    paginator = Paginator(post_list, POSTS_ON_PAGE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    post_list = group.posts.select_related('author')
    paginator = Paginator(post_list, POSTS_ON_PAGE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'group': group,
        'page_obj': page_obj,
    }
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    posts = author.posts.select_related('group')
    paginator = Paginator(posts, POSTS_ON_PAGE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    following = False
    if request.user.is_authenticated:
        following = request.user.follower.filter(author=author).exists()
    context = {
        'author': author,
        'page_obj': page_obj,
        'following': following,
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    comments = post.comments.select_related('author')
    form = CommentForm()
    context = {
        'post': post,
        'comments': comments,
        'form': form,
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    form = PostForm(
        request.POST or None,
        files=request.FILES or None
    )
    context = {
        'form': form
    }

    if not request.method == 'POST':
        return render(request, 'posts/create_post.html', context)
    if not form.is_valid():
        return render(request, 'posts/create_post.html', context)

    post = form.save(commit=False)
    post.author = request.user
    post.save()
    return redirect('posts:profile', request.user)


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if post.author != request.user:
        return redirect('posts:post_detail', post_id=post_id)

    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )
    context = {
        'form': form,
        'is_edit': True,
    }

    if not request.method == 'POST':
        return render(request, 'posts/create_post.html', context)
    if not form.is_valid():
        return render(request, 'posts/create_post.html', context)

    form.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    post_list = Post.objects.filter(author__following__user=request.user)
    paginator = Paginator(post_list, POSTS_ON_PAGE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    follow_author = get_object_or_404(User, username=username)
    if follow_author != request.user and (
        not request.user.follower.filter(author=follow_author).exists()
    ):
        Follow.objects.create(
            user=request.user,
            author=follow_author
        )
    return redirect('posts:profile', username)


@login_required
def profile_unfollow(request, username):
    follow_author = get_object_or_404(User, username=username)
    follow = request.user.follower.filter(author=follow_author)
    if follow.exists():
        follow.delete()
    return redirect('posts:profile', username)
