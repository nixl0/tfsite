from datetime import datetime
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout, get_user
from core.models import PersonalizedUser, Post, Like, Comment
from PIL import Image
import tensorflow as tf

def register_user(request):
    if request.method == 'POST':
        user = User.objects.create_user(request.POST['username'], request.POST['email'], request.POST['password'])
        user.save()
        
        new_user = User.objects.get(username=user.username)
        PersonalizedUser.objects.create(interests='', user_id=new_user.id)

        return redirect('home')
    else:
        return render(request, 'register.html')


def login_user(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)

            return redirect('home')
        else:
            return HttpResponse('invalid login')
    else:
        return render(request, 'login.html')
    

def logout_user(request):
    logout(request)

    return redirect('home')


def profile(request):
    authenticated_user = get_user(request)
    personalized_user = PersonalizedUser.objects.get(user_id=authenticated_user.id)
    # Поскольку PersonalizedUser дублирует User, но содержит дополнительное поле interests, мы достаём и его

    return render(request, 'profile.html', { 'authenticated_user': authenticated_user, 'personalized_user': personalized_user })


def home(request):
    try:
        pertinent_post_ids = get_pertinent_posts(request)

        pertinent_posts = list()
        for pertinent_post_id in pertinent_post_ids:
            pertinent_posts.append(Post.objects.get(id=pertinent_post_id[0]))

        return render(request, 'home.html', { 'posts': pertinent_posts })
    except:
        posts = Post.objects.all()

        return render(request, 'home.html', { 'posts': posts })


def post_add(request):
    if request.method == 'POST':
        """
        tags > formatted
        desc > same
        image > pasted
        highlights > analyzed and gathered
        author > id extracted
        """

        formatted_tags = request.POST['tags'].replace(' ', '')
        
        highlights = ''
        data = analyze(request.FILES['image'])
        for x, option in enumerate(data):
            if x == 0:
                highlights = highlights + option['label']
            else:
                highlights = highlights + ',' + option['label']

        author = get_user(request)

        post = Post(
                tags=formatted_tags,
                desc=request.POST['desc'],
                image=request.FILES['image'],
                highlights=highlights,
                author=author
            )
        
        post.save()

        return redirect('home')
    else:
        return render(request, 'add.html')


def post_view(request, id):
    author = get_user(request)
    author_id = author.id
    post = Post.objects.get(id=id)

    try:
        is_liked = Like.objects.filter(author=author, post=post)
    except:
        is_liked = None

    try:
        likes_count = Like.objects.filter(post=post).count()
    except:
        likes_count = None

    try:
        comments_count = Comment.objects.filter(post=post).count()
    except:
        comments_count = None

    try:
        comments = Comment.objects.filter(post=post)
    except:
        comments = None

    remember(request, post.highlights, 1, 1)

    return render(request, 'view.html', { 'post': post,
                                         'is_liked': is_liked,
                                         'likes_count': likes_count,
                                         'comments_count': comments_count,
                                         'comments': comments,
                                         'author_id': author_id
                                         })


def post_like(request, id):
    author = get_user(request)
    post = Post.objects.get(id=id)

    like = Like(author=author, post=post)
    like.save()

    remember(request, post.highlights, 10, 5)

    return redirect(f'/post/{id}/')


def post_comment(request, id):
    author = get_user(request)
    post = Post.objects.get(id=id)

    comment = Comment(
        author=author,
        post=post,
        body=request.POST['body'],
        timestamp=datetime.now()
        )
    comment.save()

    remember(request, post.highlights, 50, 10)

    return redirect(f'/post/{id}/')


def analyze(image):
    # С помощью TensorFlow анализ десяти самых подходящих "хайлайтов"

    img = Image.open(image)
    img = img.resize((224, 224))
    img_array = tf.keras.preprocessing.image.img_to_array(img)
    img_array = tf.expand_dims(img_array, 0)

    # Загрузка модели VGG16
    model = tf.keras.applications.VGG16(include_top=True, weights='imagenet')

    # Предсказание класса изображения
    predictions = model.predict(img_array)
    results = tf.keras.applications.vgg16.decode_predictions(predictions, top=10)

    data = []
    for result in results[0]:
        label = result[1]
        probability = round(float(result[2]), 3)
        data.append({
            'label': label,
            'probability': probability
        })

    return data


def remember(request, highlights_str, add_weight, sub_weight):
    # Во время просмотра поста, сохранение "хайлайтов" просматриваемого поста в "интересы" пользователя

    authenticated_user = get_user(request)
    personalized_user = PersonalizedUser.objects.get(user_id=authenticated_user.id)

    interests_str = personalized_user.interests

    if interests_str == '':
        # Если у пользователя ещё нет "интересов"

        highlights_arr = split_highlights(highlights_str)
        shaped_interests_str = shape_interests(highlights_arr)

        personalized_user.interests = shaped_interests_str
    else:
        # Если у пользователя уже есть "интересы"

        interests_arr = split_interests(interests_str)
        highlights_arr = split_highlights(highlights_str)

        # Предварительно сортируем список словарей по весу
        interests_arr = sorted(interests_arr, key=lambda interest_dict: int(interest_dict['weight']), reverse=True)


        for highlight in highlights_arr:
            global highlight_in_interests
            highlight_in_interests = False

            for interest in interests_arr:

                if interest['title'] == highlight:
                    # Такой хайлайт есть в интересах. Увеличиваем вес

                    highlight_in_interests = True

                    if int(interest['weight']) >= 999:
                        # Если вес сравнялся с 999, ничего не делаем
                        
                        pass
                    else:
                        # Если вес меньше 999, прибавляем к весу 2, потому что дальше будем отнимать 1
                        interest['weight'] = str(int(interest['weight']) + (add_weight + 1))

            if not highlight_in_interests:
                # Если хайлайта нету в интересах
                # То такого хайлайта в интересах нету. Добавляем

                if len(interests_arr) == 100:
                    # Если список интересов пользователя заполнен (есть все 100 значений)
                    # То заменяем самый последний элемент

                    interests_arr[-1] = { 'title': highlight, 'weight': str(add_weight + 1) }
                else:
                    # Если список интересов пользователя НЕ заполнен (меньше 100 значений)
                    # То добавляем элемент к концу

                    interests_arr.append({ 'title': highlight, 'weight': str(add_weight + 1) })

        for interest in interests_arr:
            # Отнимаем от всех интересов одно (1) значение
            interest['weight'] = str(int(interest['weight']) - sub_weight)

            if int(interest['weight']) <= 0:
                # Если в конце выходит, что у какого-то элемента вес выходит 0 или меньше
                # То удаляем этот элемент
                interests_arr.remove(interest)

        joined_interests_str = join_interests(interests_arr)

        personalized_user.interests = joined_interests_str
    
    personalized_user.save()


def get_pertinent_posts(request):
    authenticated_user = get_user(request)
    personalized_user = PersonalizedUser.objects.get(user_id=authenticated_user.id)
    interests_str = personalized_user.interests
    interests_arr = split_interests(interests_str)

    posts_arr = Post.objects.all()

    post_pertinences_arr = list()
    
    for post in posts_arr:

        post_pertinence_num = 0

        highlights_arr = split_highlights(post.highlights)
        
        for highlight in highlights_arr:
            for interest in interests_arr:

                if highlight == interest['title']:
                    # Если хайлайт находится в интересах
                    # Запоминаем вес интереса

                    post_pertinence_num = post_pertinence_num + int(interest['weight'])

        post_pertinence = [ post.id, post_pertinence_num ]

        post_pertinences_arr.append(post_pertinence)
        
    post_pertinences_arr = sorted(post_pertinences_arr, key=lambda x: int(x[1]), reverse=True)
        
    return post_pertinences_arr


def shape_interests(highlights_arr) -> str:
    interests_str = ''

    for x, highlight in enumerate(highlights_arr):
        if x == 0:
            interests_str = interests_str + f'{highlight}:1'
        else:
            interests_str = interests_str + f',{highlight}:1'

    return interests_str


def split_interests(interests_str) -> list:
    interests_arr = list()

    interests_arr_undivided = interests_str.split(',')
    for interest in interests_arr_undivided:
        title, weight = interest.split(':')

        interests_arr.append({ 'title': title, 'weight': weight })
    
    return interests_arr


def join_interests(interests_arr) -> str:
    interests_str = ''

    for x, interest in enumerate(interests_arr):
        if x == 0:
            interests_str = interest['title'] + ':' + interest['weight']
        else:
            interests_str = interests_str + ',' + interest['title'] + ':' + interest['weight']

    return interests_str


def split_highlights(highlights_str) -> list:
    return highlights_str.split(',')


def join_highlights(highlights_arr) -> str:
    return highlights_arr.join(',')