<template>
    <div class = Person>
        <h1>这是H1-显示名字</h1>
        <h2>名字：{{name}}</h2>
        <h2>年龄：{{age}}</h2>
        <button @click = "changeName">修改名字</button> 
        <!-- 将下面定义的方法changeName绑定到“修改名字”按钮，这样就能通过点击来调用函数 -->
        <button @click = "changeAge">修改年龄</button>
        <button @click = "showTele">显示电话</button>
    </div>      
</template>

<!-- 语法糖写法，把setup独立在 script外。但是仍然需要script标签来定义组件名字-->
<script lang = "ts">
    export default {
        name: 'Person'
    }
</script>
<!-- 
另外一种不需要再写一个script的方法是用  vite-plugin-vue-setup-extend 插件
1. 下载：npm i vite-plugin-vue-setup-extend -D
2. 然后在vite.config.ts中引入并使用：
    import { defineConfig } from 'vite'
    import VueSetupExtend from 'vite-plugin-vue-setup-extend'

    export default defineConfig({
    plugins: [ VueSetupExtend() ]
    }) 

3. 然后就不需要上面那个script标签了，只需要在setup标签上加name属性即可：
    <script setup lang="ts" name="Person">
-->

<!--将setup独立出来-->
<script setup lang = 'ts'>
    
    let name = '张三';
    let age = 18;
    let tele = '12345678901';

    function changeName(){
        name = 'Zhang San'; 
    };                 

    function changeAge(){
        age +=1;  
    };

    function showTele(){
        alert(tele);   
    };

    return {name,age,changeName,changeAge,showTele};
</script>