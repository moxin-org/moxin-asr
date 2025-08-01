import { createRouter, createWebHistory, RouteRecordRaw } from 'vue-router';

import NotFoundVue from '@/views/404/index.vue';
import WelcomeVue from '@/views/Welcome/index.vue';
import HomeVue from '@/views/Home/index.vue';
import SettingsVue from '@/views/Settings/index.vue';

const routes: Array<RouteRecordRaw> = [
  {
    name:"welcome",
    path: '/',
    component: WelcomeVue,
    meta: {
      requiresAgreement: false,
    }
  },
  {
    name: "home",
    path: '/home',
    component: HomeVue,
  },
  {
    name:"settings",
    path:'/settings',
    component: SettingsVue,
  },
  {
    name:"404",
    path:'/404',
    component: NotFoundVue,
  }
];

const router = createRouter({
  // history: createWebHistory(),
  history: createWebHistory('/app/'),
  routes,
});

router.beforeEach((to, from, next) => {
  console.log('=============== router to : ', to)
  if (to.matched.length === 0) {
    next({ name: '404' });
  } else {
    next();
  }
});

export default router;
