<?php

$configPath = __DIR__ . '/config.local.php';
$config = is_file($configPath) ? require $configPath : [];

if (!is_array($config)) {
    throw new RuntimeException('config.local.php must return an array.');
}

$collection = $config['collection'] ?? __DIR__ . '/collection';

if (!is_string($collection) || $collection === '' || $collection[0] !== '/') {
    throw new RuntimeException('Collection must be an absolute filesystem path.');
}

if (!is_dir($collection) || !is_readable($collection)) {
    throw new RuntimeException('Collection directory must exist and be readable.');
}

$formats = '*.jpg,*.jpeg,*.JPG,*.png,*.gif';
$priorities = array();

// ####################

function globalize($fileName, $fullPath)
{
    if ($fileName[0] != '/') {
        return "$fullPath/$fileName";
    }

    return $fileName;
}

function getWeightedRandomSample($weights, $arr)
{
    $totalWeightDefined = array_sum($weights);
    $undefinedWeight = ($totalWeightDefined <= 100) ? (100 - $totalWeightDefined) / (count($arr) - count($weights)) : 0;

    foreach ($arr as $i) {
        if (!isset($weights[$i])) {
            $weights[$i] = $undefinedWeight;
        }
    }

    $n = mt_rand(0, 99);

    $cumulativeWeight = 0;
    foreach ($weights as $i => $weight) {
        $cumulativeWeight += $weight;
        if ($n < $cumulativeWeight) {
            return $i;
        }
    }

    // Fallback
    return $arr[array_rand($arr)];
}

$isCli = PHP_SAPI === 'cli';
$images = glob("$collection/{{$formats}}", GLOB_BRACE);
if ($images === false || count($images) === 0) {
    throw new RuntimeException('Collection directory contains no matching images.');
}

if ($isCli) {
    echo("Choosing from:");
    print_r($images);
    echo("\n");
}

if (count($priorities) == 0) {
    if ($isCli) {
        echo("Going the easy way\n");
    }

    $image = $images[array_rand($images)];
} else {
    if ($isCli) {
        echo("Going the hard way\n");
    }

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
