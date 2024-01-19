<?php

$dir = '/var/www/html/snootberg/collection'; // replace with your directory
$images = glob("$dir/{*.jpg,*.png,*.gif}", GLOB_BRACE); // find all images
$image = array_rand($images); // select random image

header("Content-Type: image/jpeg");
readfile($images[$image]);

?>
