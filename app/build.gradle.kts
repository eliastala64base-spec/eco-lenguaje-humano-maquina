plugins { id("com.android.application"); id("org.jetbrains.kotlin.android") }
android {
 namespace="pe.elias.cidelsaqc"; compileSdk=35
 defaultConfig { applicationId="pe.elias.cidelsaqc"; minSdk=29; targetSdk=35; versionCode=1; versionName="1.0" }
 compileOptions { sourceCompatibility=JavaVersion.VERSION_17; targetCompatibility=JavaVersion.VERSION_17 }
 kotlinOptions { jvmTarget="17" }
}
dependencies {
 implementation("androidx.core:core-ktx:1.15.0"); implementation("androidx.appcompat:appcompat:1.7.0"); implementation("androidx.activity:activity-ktx:1.10.0")
 implementation("androidx.camera:camera-core:1.4.1"); implementation("androidx.camera:camera-camera2:1.4.1"); implementation("androidx.camera:camera-lifecycle:1.4.1"); implementation("androidx.camera:camera-view:1.4.1")
 implementation("androidx.exifinterface:exifinterface:1.3.7")
}
