<?php
ini_set('display_errors', 1);
ini_set('display_startup_errors', 1);
error_reporting(E_ALL);
 
$db = new SQLite3('grow.db');
if(ISSET($_POST['lightson'])) {
$updatequery = "UPDATE settings SET lightson='";
$updatequery .= $_POST['lightson'];
$updatequery .= "', lightsoff='";
$updatequery .= $_POST['lightsoff'];
$updatequery .= "', pumprun=";
$updatequery .= $_POST['pumprun'];
$updatequery .= ", pumpinter=";
$updatequery .= $_POST['pumpinter'];
$updatequery .= ", fantemp=";
$updatequery .= $_POST['fantemp'];
$updatequery .= ", heattemp=";
$updatequery .= $_POST['heattemp'];
$updatequery .= ", fanhumid=";
$updatequery .= $_POST['fanhumid'];
$updatequery .= ", humidhumid=";
$updatequery .= $_POST['humidhumid'];
$updatequery .= ", dehumidhumid=";
$updatequery .= $_POST['dehumidhumid'];
$updatequery .= ", lightsenab=";
$updatequery .= $_POST['lightsenab'];
$updatequery .= ", fanenab=";
$updatequery .= $_POST['fanenab'];
$updatequery .= ", humidenab=";
$updatequery .= $_POST['humidenab'];
$updatequery .= ", heatenab=";
$updatequery .= $_POST['heatenab'];
$updatequery .= ", dehumidenab=";
$updatequery .= $_POST['dehumidenab'];
$updatequery .= ", pumpenab=";
$updatequery .= $_POST['pumpenab'];
$updatequery .= ", sensortype='";
$updatequery .= $_POST['sensortype'];
$updatequery .= "';";
$update = $db->query($updatequery);
}
?>
<!DOCTYPE html>
<html lang="en">
<head>
<style>
table {
  border: 0px;
  border-collapse: collapse;
  width: 100%;
}
tr:nth-child(even) {
  background-color: #DDEEDD;
}
td {
  border: 1px solid black;
}
div {
  overflow-y: auto;
}
</style>
<link rel="icon" type="image/x-icon" href="favicon.png">
<title>GrowBox Dashboard</title>
</head>
<body>
<h1>GrowBox Dashboard</h1>
<div>
Current Settings:
<form action="grow.php" method="POST">
<table>
<tr>
<td style="text-align: right;">Time Lights On:</td>
<td><input type="text" name="lightson" value="<?php 
$result1 = $db->querySingle('SELECT * FROM settings;',True);
echo $result1['lightson'];
?>"></td>
<td rowspan=16>
<img height=512 width=256 src="./images/<?php 
$latestimg = $db->querySingle('SELECT picfile FROM environment ORDER BY rowid DESC;', True);
echo $latestimg['picfile'];
?>">
</td>
</tr><tr>
<td style="text-align: right;">Time Lights Off:</td>
<td><input type="text" name="lightsoff" value="<?php echo $result1['lightsoff']; ?>"></td>
</tr><tr>
<td style="text-align: right;">Pump Run time Seconds:</td>
<td><input type="text" name="pumprun" value="<?php echo $result1['pumprun']; ?>"></td>
</tr><tr>
<td style="text-align: right;">Pump Interval Seconds:</td>
<td><input type="text" name="pumpinter" value="<?php echo $result1['pumpinter']; ?>"></td>
</tr><tr>
<td style="text-align: right;">Fan Activation Temp:</td>
<td><input type="text" name="fantemp" value="<?php echo $result1['fantemp']; ?>"></td>
</tr><tr>
<td style="text-align: right;">Heating Pad Deactivation Temp:</td>
<td><input type="text" name="heattemp" value="<?php echo $result1['heattemp']; ?>"></td>
</tr><tr>
<td style="text-align: right;">Fan Activation humidity:</td>
<td><input type="text" name="fanhumid" value="<?php echo $result1['fanhumid']; ?>"></td>
</tr><tr>
<td style="text-align: right;">Humidifier Activation Humidity:</td>
<td><input type="text" name="humidhumid" value="<?php echo $result1['humidhumid']; ?>"></td>
</tr><tr>
<td style="text-align: right;">Dehumidifier Activation Humidity:</td>
<td><input type="text" name="dehumidhumid" value="<?php echo $result1['dehumidhumid']; ?>"></td>
</tr><tr>
<td style="text-align: right;">Lights:</td>
<td>
<select name="lightsenab" autocomplete="off">
<option value="1" label="Enabled"<?php if((bool)$result1['lightsenab']) echo ' selected="True"'; ?>>
<option value="0" label="Disabled"<?php if(!(bool)$result1['lightsenab']) echo ' selected="True"'; ?>>
</select>
</td>
</tr><tr>
<td style="text-align: right;">Fan:</td>
<td>
<select name="fanenab" autocomplete="off">
<option value="1" label="Enabled"<?php if((bool)$result1['fanenab']) echo ' selected="True"'; ?>>
<option value="0" label="Disabled"<?php if(!(bool)$result1['fanenab']) echo ' selected="True"'; ?>>
</select>
</td>
</tr><tr>
<td style="text-align: right;">Humidifier:</td>
<td>
<select name="humidenab" autocomplete="off">
<option value="1" label="Enabled"<?php if((bool)$result1['humidenab']) echo ' selected="True"'; ?>>
<option value="0" label="Disabled"<?php if(!(bool)$result1['humidenab']) echo ' selected="True"'; ?>>
</select>
</td>
</tr><tr>
<td style="text-align: right;">Heaters:</td>
<td>
<select name="heatenab" autocomplete="off">
<option value="1" label="Enabled"<?php if((bool)$result1['heatenab']) echo ' selected="True"'; ?>>
<option value="0" label="Disabled"<?php if(!(bool)$result1['heatenab']) echo ' selected="True"'; ?>>
</select>
</td>
</tr><tr>
<td style="text-align: right;">Dehumidifier:</td>
<td>
<select name="dehumidenab" autocomplete="off">
<option value="1" label="Enabled"<?php if((bool)$result1['dehumidenab']) echo ' selected="True"'; ?>>
<option value="0" label="Disabled"<?php if(!(bool)$result1['dehumidenab']) echo ' selected="True"'; ?>>
</select>
</td>
</tr><tr>
<td style="text-align: right;">Pump:</td>
<td>
<select name="pumpenab" autocomplete="off">
<option value="1" label="Enabled"<?php if((bool)$result1['pumpenab']) echo ' selected="True"'; ?>>
<option value="0" label="Disabled"<?php if(!(bool)$result1['pumpenab']) echo ' selected="True"'; ?>>
</select>
</td>
</tr><tr>
<td style="text-align: right;">Sensor type:</td>
<td>
<select name="sensortype" autocomplete="off">
<option value="SHT30" label="SHT30"<?php if($result1['sensortype'] == "SHT30") echo ' selected="True"'; ?>>
<option value="DHT22" label="DHT22"<?php if($result1['sensortype'] == "DHT22") echo ' selected="True"'; ?>>
</select>
</td>
</tr>
<tr><td></td><td><input type="submit" value="Update Settings"></td></tr>
</table>
</form>
</div>
<div>
<table>
<tr>
<td>Time</td><td>Temp</td><td>Humidity</td><td>Relay Mask<br>L | F | Hu | Ht | D | P</td><td>Picture Link</td>
</tr>
<?php
$result2 = $db->query('SELECT * FROM environment ORDER BY rowid DESC;');
$stopafter=1500;
while($stopafter > 0 && $envreadings = $result2->fetchArray(SQLITE3_ASSOC)) {
	echo "<tr><td>";
	echo $envreadings['time'];
	echo "</td><td>";
	echo round(floatval($envreadings['temp']));
	echo "</td><td>";
	echo round(floatval($envreadings['humid']));
	echo "</td><td>";
	echo $envreadings['relaymask'];
	echo '</td><td><a href="./images/';
	echo $envreadings['picfile'];
	echo '">';
	echo $envreadings['picfile'];
	echo "</a></td>";
	//echo '<td><img src="';
	//echo substr($envreadings['picfile'],1);
	//echo '" width="64" height="64" alt="thumbnail"></td>';
	echo "</tr>";
	echo "\n";
	$stopafter--;
}
?>
</table>
</div>
</body>
</html>
