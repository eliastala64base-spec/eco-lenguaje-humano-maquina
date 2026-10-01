package pe.elias.cidelsaqc

import android.Manifest
import android.app.AlertDialog
import android.content.ContentValues
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.graphics.*
import android.graphics.drawable.Drawable
import android.net.Uri
import android.os.Bundle
import android.provider.MediaStore
import android.view.Gravity
import android.view.View
import android.widget.*
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AppCompatActivity
import androidx.appcompat.content.res.AppCompatResources
import androidx.camera.core.*
import androidx.camera.lifecycle.ProcessCameraProvider
import androidx.camera.view.PreviewView
import androidx.core.content.ContextCompat
import androidx.exifinterface.media.ExifInterface
import java.io.File
import java.text.SimpleDateFormat
import java.util.*
import java.util.concurrent.Executors

private fun Context.dp(n:Int)=(n*resources.displayMetrics.density).toInt()
private class Prefs(c:Context){
 private val s=c.getSharedPreferences("stamp",0)
 var a:String
  get()=s.getString("a","CONTROL DE CALIDAD")!!
  set(v){s.edit().putString("a",v).apply()}
 var b:String
  get()=s.getString("b","Control dimensiones de acero de construcción")!!
  set(v){s.edit().putString("b",v).apply()}
 var text:Int
  get()=s.getInt("text",32)
  set(v){s.edit().putInt("text",v).apply()}
 var logo:Int
  get()=s.getInt("logo",28)
  set(v){s.edit().putInt("logo",v).apply()}
 var alpha:Int
  get()=s.getInt("alpha",100)
  set(v){s.edit().putInt("alpha",v).apply()}
 var time:Boolean
  get()=s.getBoolean("time",true)
  set(v){s.edit().putBoolean("time",v).apply()}
 var uri:String?
  get()=s.getString("uri",null)
  set(v){s.edit().putString("uri",v).apply()}
}
private fun logo(c:Context,u:String?):Bitmap?{
 if(!u.isNullOrBlank()) try{c.contentResolver.openInputStream(Uri.parse(u)).use{return BitmapFactory.decodeStream(it)}}catch(_:Exception){}
 val d=AppCompatResources.getDrawable(c,R.drawable.cidelsa_logo)?:return null
 val w=1280; val h=(w*(d.intrinsicHeight.toFloat()/d.intrinsicWidth)).toInt().coerceAtLeast(1)
 return Bitmap.createBitmap(w,h,Bitmap.Config.ARGB_8888).also{val x=Canvas(it);d.setBounds(0,0,w,h);d.draw(x)}
}
private fun stamp(c:Canvas,w:Int,h:Int,p:Prefs,l:Bitmap?,d:Date){
 val m=w*.025f
 l?.let{val dw=w*p.logo/100f;val dh=it.height*dw/it.width;val q=Paint(Paint.ANTI_ALIAS_FLAG or Paint.FILTER_BITMAP_FLAG);q.alpha=(255*p.alpha/100f).toInt();c.drawBitmap(it,null,RectF(m,m,m+dw,m+dh),q)}
 val size=w*p.text/1000f;val normal=Paint(Paint.ANTI_ALIAS_FLAG).apply{color=Color.WHITE;textAlign=Paint.Align.RIGHT;textSize=size;typeface=Typeface.DEFAULT;setShadowLayer(size*.13f,2f,2f,Color.BLACK)};val bold=Paint(normal).apply{typeface=Typeface.DEFAULT_BOLD}
 val lines=mutableListOf<Pair<String,Boolean>>();if(p.a.isNotBlank())lines+=p.a to true;if(p.b.isNotBlank())lines+=p.b to false;lines+=SimpleDateFormat(if(p.time)"dd/MM/yyyy  HH:mm:ss" else "dd/MM/yyyy",Locale.getDefault()).format(d) to true
 var y=h-m;for((t,z) in lines.asReversed()){val q=Paint(if(z)bold else normal);while(q.measureText(t)>w*.84f&&q.textSize>size*.6f)q.textSize*=.94f;c.drawText(t,w-m,y,q);y-=size*1.3f}
}
private class Overlay(c:Context):View(c){private val p=Prefs(c);private var l=logo(c,p.uri);fun reload(){l?.recycle();l=logo(context,p.uri);invalidate()};override fun onDraw(c:Canvas){stamp(c,width,height,p,l,Date());postInvalidateDelayed(1000)}}

class MainActivity:AppCompatActivity(){
 private lateinit var pv:PreviewView;private lateinit var ov:Overlay;private lateinit var status:TextView;private lateinit var shot:Button;private var cap:ImageCapture?=null;private val ex=Executors.newSingleThreadExecutor();private val p by lazy{Prefs(this)}
 private val camPerm=registerForActivityResult(ActivityResultContracts.RequestPermission()){if(it)camera()else Toast.makeText(this,"Autoriza la cámara",Toast.LENGTH_LONG).show()}
 private val picker=registerForActivityResult(ActivityResultContracts.OpenDocument()){u:Uri?->if(u!=null){try{contentResolver.takePersistableUriPermission(u,Intent.FLAG_GRANT_READ_URI_PERMISSION)}catch(_:Exception){};p.uri=u.toString();ov.reload();Toast.makeText(this,"Logo actualizado",Toast.LENGTH_SHORT).show()}}
 override fun onCreate(b:Bundle?){super.onCreate(b);val r=FrameLayout(this);pv=PreviewView(this).apply{scaleType=PreviewView.ScaleType.FILL_CENTER};ov=Overlay(this);r.addView(pv,FrameLayout.LayoutParams(-1,-1));r.addView(ov,FrameLayout.LayoutParams(-1,-1));
  val adj=Button(this).apply{text="AJUSTES";setOnClickListener{settings()}};r.addView(adj,FrameLayout.LayoutParams(dp(120),dp(52),Gravity.TOP or Gravity.END).apply{topMargin=dp(14);rightMargin=dp(14)})
  val bot=LinearLayout(this).apply{orientation=LinearLayout.VERTICAL;gravity=Gravity.CENTER};status=TextView(this).apply{text="Listo";setTextColor(Color.WHITE)};shot=Button(this).apply{text="●";textSize=40f;setOnClickListener{take()}};bot.addView(status);bot.addView(shot,LinearLayout.LayoutParams(dp(86),dp(86)));r.addView(bot,FrameLayout.LayoutParams(-1,dp(125),Gravity.BOTTOM));setContentView(r)
  if(ContextCompat.checkSelfPermission(this,Manifest.permission.CAMERA)==PackageManager.PERMISSION_GRANTED)camera()else camPerm.launch(Manifest.permission.CAMERA)}
 private fun camera(){val f=ProcessCameraProvider.getInstance(this);f.addListener({try{val pr=f.get();val pre=Preview.Builder().build().also{it.setSurfaceProvider(pv.surfaceProvider)};cap=ImageCapture.Builder().setCaptureMode(ImageCapture.CAPTURE_MODE_MINIMIZE_LATENCY).build();pr.unbindAll();pr.bindToLifecycle(this,CameraSelector.DEFAULT_BACK_CAMERA,pre,cap);status.text="Listo"}catch(e:Exception){status.text="Error cámara"}},ContextCompat.getMainExecutor(this))}
 private fun take(){val x=cap?:return;x.targetRotation=pv.display.rotation;val d=Date();val f=File.createTempFile("raw_",".jpg",cacheDir);shot.isEnabled=false;status.text="Capturando...";x.takePicture(ImageCapture.OutputFileOptions.Builder(f).build(),ContextCompat.getMainExecutor(this),object:ImageCapture.OnImageSavedCallback{override fun onImageSaved(o:ImageCapture.OutputFileResults){ex.execute{try{save(f,d);runOnUiThread{status.text="Foto guardada";shot.isEnabled=true;Toast.makeText(this@MainActivity,"Guardada en Pictures/CIDELSA_QC",Toast.LENGTH_SHORT).show()}}catch(e:Exception){runOnUiThread{status.text="Error";shot.isEnabled=true;Toast.makeText(this@MainActivity,e.message,Toast.LENGTH_LONG).show()}}finally{f.delete()}}};override fun onError(e:ImageCaptureException){f.delete();shot.isEnabled=true;status.text="Error"}})}
 private fun save(f:File,d:Date){val raw=BitmapFactory.decodeFile(f.path)?:error("No se pudo leer la foto");val o=ExifInterface(f.path).getAttributeInt(ExifInterface.TAG_ORIENTATION,ExifInterface.ORIENTATION_NORMAL);val deg=when(o){ExifInterface.ORIENTATION_ROTATE_90->90f;ExifInterface.ORIENTATION_ROTATE_180->180f;ExifInterface.ORIENTATION_ROTATE_270->270f;else->0f};val b=if(deg==0f)raw else Bitmap.createBitmap(raw,0,0,raw.width,raw.height,Matrix().apply{postRotate(deg)},true).also{raw.recycle()};val out=b.copy(Bitmap.Config.ARGB_8888,true);if(out!==b)b.recycle();val l=logo(this,p.uri);stamp(Canvas(out),out.width,out.height,p,l,d);l?.recycle();val v=ContentValues().apply{put(MediaStore.Images.Media.DISPLAY_NAME,"CIDELSA_QC_"+SimpleDateFormat("yyyyMMdd_HHmmss",Locale.US).format(d)+".jpg");put(MediaStore.Images.Media.MIME_TYPE,"image/jpeg");put(MediaStore.Images.Media.RELATIVE_PATH,"Pictures/CIDELSA_QC");put(MediaStore.Images.Media.IS_PENDING,1)};val u=contentResolver.insert(MediaStore.Images.Media.EXTERNAL_CONTENT_URI,v)?:error("No se pudo guardar");contentResolver.openOutputStream(u)!!.use{out.compress(Bitmap.CompressFormat.JPEG,95,it)};v.clear();v.put(MediaStore.Images.Media.IS_PENDING,0);contentResolver.update(u,v,null,null);out.recycle()}
 private fun settings(){val box=LinearLayout(this).apply{orientation=LinearLayout.VERTICAL;setPadding(dp(20),dp(4),dp(20),0)};val e1=EditText(this).apply{setText(p.a);hint="Línea 1"};val e2=EditText(this).apply{setText(p.b);hint="Línea 2"};val tm=Switch(this).apply{text="Mostrar hora";isChecked=p.time};val tl=TextView(this);val ts=SeekBar(this).apply{max=70;progress=p.text};val ll=TextView(this);val ls=SeekBar(this).apply{max=60;progress=p.logo};val al=TextView(this);val asb=SeekBar(this).apply{max=100;progress=p.alpha};fun labels(){tl.text="Tamaño texto: ${ts.progress.coerceAtLeast(15)/10f}%";ll.text="Tamaño logo: ${ls.progress.coerceAtLeast(10)}%";al.text="Opacidad logo: ${asb.progress.coerceAtLeast(20)}%"};val li=object:SeekBar.OnSeekBarChangeListener{override fun onProgressChanged(s:SeekBar?,x:Int,b:Boolean){labels()};override fun onStartTrackingTouch(s:SeekBar?){};override fun onStopTrackingTouch(s:SeekBar?){}};ts.setOnSeekBarChangeListener(li);ls.setOnSeekBarChangeListener(li);asb.setOnSeekBarChangeListener(li);labels();listOf(e1,e2,tm,tl,ts,ll,ls,al,asb).forEach{box.addView(it)};box.addView(Button(this).apply{text="CAMBIAR LOGO";setOnClickListener{picker.launch(arrayOf("image/*"))}});box.addView(Button(this).apply{text="USAR LOGO CIDELSA";setOnClickListener{p.uri=null;ov.reload();Toast.makeText(this@MainActivity,"Logo CIDELSA restaurado",Toast.LENGTH_SHORT).show()}});AlertDialog.Builder(this).setTitle("Ajustes del sello").setView(ScrollView(this).apply{addView(box)}).setPositiveButton("GUARDAR"){_,_->p.a=e1.text.toString();p.b=e2.text.toString();p.time=tm.isChecked;p.text=ts.progress.coerceAtLeast(15);p.logo=ls.progress.coerceAtLeast(10);p.alpha=asb.progress.coerceAtLeast(20);ov.reload()}.setNegativeButton("CANCELAR",null).show()}
 override fun onDestroy(){super.onDestroy();ex.shutdown()}
}
