<?php

$collection = __DIR__ . '/collection';
$formats = '*.jpg,*.jpeg,*.JPG,*.png,*.gif';
$priorities = array();

// ####################

function globalize($fileName, $fullPath) {
    if($fileName[0] != '/') {
        return "$fullPath/$fileName";
    }

    return $fileName;
}

function getWeightedRandomSample($weights, $arr) {
    $totalWeightDefined = array_sum($weights);
    $undefinedWeight = ($totalWeightDefined <= 100) ? (100 - $totalWeightDefined) / (count($arr) - count($weights)) : 0;

    foreach($arr as $i) {
        if(!isset($weights[$i])) $weights[$i] = $undefinedWeight;
    }

    $n = mt_rand(0, 99);

    $cumulativeWeight = 0;
    foreach($weights as $i => $weight) {
        $cumulativeWeight += $weight;
        if($n < $cumulativeWeight) return $i;
    }

    // Fallback
    return $arr[array_rand($arr)];
}

$isCli = PHP_SAPI === 'cli';
$images = glob("$collection/{{$formats}}", GLOB_BRACE);

if ($isCli) {
    echo("Choosing from:");
    print_r($images);
    echo("\n");
}

if (count($priorities) == 0) {
    if ($isCli) echo("Going the easy way\n");

    $image = $images[array_rand($images)];
} else {
    if ($isCli) echo("Going the hard way\n");

    $image = globalize(
        getWeightedRandomSample($priorities, $images),
        $collection
    );
}

if ($isCli) {
    echo("Chosen $image\n");
    exit(0);
}

header('Content-Type: image/jpeg');
readfile($image);
