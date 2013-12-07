blogae
======
Personal blogging platform for Google App Engine.


Description
-----------
This project is to run a blog of an admin and multiple authors in a GAE (Google App Engine) instance. A GAE instance has enough free quota to run a single blog in many cases. If yours uses more than the free quota, you can pay only for what you used. (Or pay nothing and wait for the daily quota refresh.)


Features
--------

 * A GAE instance is handling only one blog. So, the admin UI is very simple and clean.
 * Supports many list views. Yearly, monthly, tag, and search views.
 * Supports Atom feed.
 * Live preview in editor view.
 * Supports photo section from G+ photos (a.k.a. Picasa). And yes, you can select your non-public photos too. It requires some extra configuration in your GAE and blogae configs.
 * No native support for commenting. The blogae is focusing on writing posts. You still use 3rd party commenting tools like disqus. You can also use other social tools like Google +1, Facebook Like, Tweet buttons. See the demo blog. It has all these tools.
 * User scripts to automate some of your writing. For example, you can write a script in js to sanitize some htmls that you paste into the editor.


Demo
----

 * http://blogae-demo.appspot.com - demo blog.
 * https://blogae-demo.appspot.com/admin - admin page

You can try creating a post in the demo blog. You should be able to select some photos from your Google+ albums. To do this, you need to authorize the photo picker page.


Note
----
For other information such as installation and known issues, see wiki. If you have some feedback or feature requests, please file an issue for that.


Screenshot
----------

 * Admin page.
  * <img src="https://lh5.googleusercontent.com/-uFZfQCbyJKw/UqK_PPBJydI/AAAAAAAC4Ts/Rr4nPtUB7mU/w2056-h1460-no/blogae_admin.png" width="400">
 * List view.
  * <img src="https://lh3.googleusercontent.com/-eI4kIOtsHRs/UqK_QPBvZvI/AAAAAAAC4T0/RkKi7X3ynfk/w1800-h1626-no/blogae_list.png" width="400">
 * Post view.
  * <img src="https://lh3.googleusercontent.com/-q4JoUJ6EohA/UqK_PGYig8I/AAAAAAAC4To/Ve0Eet7BD3M/w1528-h1626-no/blogae_post.png" width="400">
