from django.shortcuts import render
from blog.models import Post, Categoria

def blog(request):
    posts = Post.objects.prefetch_related('categorias').all()

    # Extraer objetos únicos de categoría por nombre
    categorias_unicas = {}
    for post in posts:
        for cat in post.categorias.all():
            categorias_unicas[cat.nombre] = cat  # sobrescribe duplicados por nombre

    context = {
        'posts': posts,
        'categorias_unicas': categorias_unicas.values(),  # lista de objetos únicos
        'meta_title': 'Blog de Desarrollo Web y Marketing Digital | Código Vivo Studio',
        'meta_description': 'Consejos sobre desarrollo web, tiendas online y posicionamiento SEO para restaurantes y comercios.',
    }
    return render(request, 'blog/blog.html', context)

def categoria(request, categoria_id):
    categoria = Categoria.objects.get(id=categoria_id)
    posts = Post.objects.filter(categorias=categoria)
    
    context = {
        "categoria": categoria, 
        "posts": posts,
        'meta_title': f'{categoria.nombre} - Blog | Código Vivo Studio',
        'meta_description': f'Artículos sobre {categoria.nombre}. Consejos y noticias del sector.',
    }
    return render(request, "blog/categoria.html", context)