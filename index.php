<?php

$collection = '/var/www/html/snootberg/collection';
$formats = '*.jpg,*.png,*.gif';
$priorities = array(
    'fox1.jpg' => 30,
);

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

$image = globalize(
    getWeightedRandomSample($priorities, $images),
    $collection
);

if ($isCli) {
    echo("Chosen $image\n");
    exit(0);
}

header('Content-Type: image/jpeg');
readfile($image);
