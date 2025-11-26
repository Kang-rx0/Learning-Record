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

<script lang = "ts">
    export default {
        name: 'Person',  // 定义组件名称，用于在其他地方import（也可以选择import整个vue文件
        setup() {
            // 在setup中定义data
            let name = '张三';
            let age = 18;
            let tele = '12345678901';

            // 在setup中定义methods
            function changeName(){
                name = 'Zhang San';  // 修改名字,能够成功修改变量，但是在页面上无法做到点击就修改（无法实时响应）
            };                 
                  // 因为这里的name是用let声明的，不是用响应式 ref或者reactive，页面不会自动更新
            function changeAge(){
                age +=1;            // 修改年龄，同上
            };

            function showTele(){
                alert(tele);       // 弹出电话
            };

            // setup中定义的变量和方法需要return出去才能在模板中直接使用
            return {name,age,changeName,changeAge,showTele}; 
        }
    }
</script>
